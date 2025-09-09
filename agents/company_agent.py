from typing import List
from pydantic import BaseModel
import re
import logging
import inspect
from models import CompanyName
from agents.ali_llm_client import AliLLMClient
from config import Config

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CompanyAgent:
    """企业识别Agent，使用LLM智能识别企业名称并归纳为正式名称"""
    
    def __init__(self):
        logger.info("企业识别模块已启动，开始初始化LLM客户端")
        # 初始化LLM客户端
        self.llm_client = AliLLMClient()
        
        # 企业识别提示词模板
        self.prompt_template = Config.AGENT_PROMPTS.get("企业识别", Config.COMPANY_PROMPT_TEMPLATE)
        
        logger.info("企业识别模块初始化完成")
    
    async def analyze_companies(self, text: str) -> List[CompanyName]:
        """
        使用LLM智能分析文本中的企业信息
        
        Args:
            text: 文本内容
            
        Returns:
            企业名称列表
        """
        logger.info(f"开始分析文本中的企业信息，文本长度: {len(text)}")
        
        if not text or not text.strip():
            logger.warning("文本为空，无法进行企业识别")
            return []
        
        try:
            # 构建企业识别提示词
            prompt = self._build_company_prompt(text)
            
            # 调用LLM进行企业识别
            generated = self.llm_client.generate_response(prompt)
            if inspect.isawaitable(generated):
                response = await generated
            else:
                response = generated
            
            logger.info(f"LLM企业识别响应: {response}")
            
            # 解析LLM响应，提取企业名称
            company_names = self._parse_company_response(response)
            
            # 去重和清理
            unique_companies = self._deduplicate_companies(company_names)
            
            logger.info(f"企业识别完成，共识别 {len(unique_companies)} 个企业")
            return unique_companies
            
        except Exception as e:
            logger.error(f"LLM企业识别失败: {str(e)}")
            # 出错时使用规则匹配作为备选方案
            return self._fallback_rule_based_extraction(text)
    
    def _build_company_prompt(self, text: str) -> str:
        """构建企业识别的提示词"""
        # 优先使用自定义提示词
        if self.prompt_template and self.prompt_template.strip():
            template = self.prompt_template
        else:
            # 使用内置的专业提示词
            template = """你是一个专业的企业信息识别专家，专门负责从新闻文本中识别和归纳企业信息。

任务要求：
1. 仔细阅读文本内容，识别所有提到的企业
2. 对于同一家公司的简称、别名、英文名等，都要归纳为同一家企业
3. 返回该企业用于工商注册的正式名称（全称）
4. 只返回企业名称，不要其他信息

识别规则：
- 识别所有企业实体，包括公司、集团、股份公司、有限公司等
- 将简称（如"阿里"）归纳为正式名称（如"阿里巴巴集团控股有限公司"）
- 将英文名（如"Apple"）归纳为中文正式名称（如"苹果公司"）
- 将子公司、分公司等归纳到母公司
- 去除重复的企业名称

输出格式：
请严格按照以下JSON格式返回，只包含企业名称数组：

```json
[
    "企业名称1",
    "企业名称2",
    "企业名称3"
]
```

注意：
- 只返回企业名称，不要其他说明
- 使用正式注册名称，不要简称
- 确保JSON格式正确
- 如果文本中没有企业，返回空数组 []

文本内容：
{content}"""

        # 将内容填充到模板中
        return self._fill_content_into_template(template, text)
    
    def _fill_content_into_template(self, template: str, content: str) -> str:
        """将内容安全地填充到模板中"""
        try:
            if template is None:
                return content

            # 优先替换双花括号占位符
            if "{{content}}" in template:
                template = template.replace("{{content}}", content)

            # 再处理单花括号占位符
            if "{content}" in template:
                template = template.replace("{content}", content)

            # 未包含占位符则直接在末尾附加内容
            return f"{template}\n\n文本内容：\n{content}"
        except Exception:
            # 任何异常下，兜底返回简单拼接
            return f"{template}\n\n{content}"
    
    def _parse_company_response(self, response: str) -> List[str]:
        """解析LLM响应，提取企业名称"""
        try:
            response = response.strip()
            
            # 尝试提取JSON格式的企业名称
            json_match = re.search(r'```json\s*(\[.*?\])\s*```', response, re.DOTALL)
            if json_match:
                import json
                try:
                    company_names = json.loads(json_match.group(1))
                    if isinstance(company_names, list):
                        return [name.strip() for name in company_names if name and name.strip()]
                except json.JSONDecodeError:
                    logger.warning("JSON解析失败，尝试其他方式提取")
            
            # 如果没有JSON格式，尝试提取数组格式
            array_match = re.search(r'\[(.*?)\]', response, re.DOTALL)
            if array_match:
                array_content = array_match.group(1)
                # 分割企业名称
                names = [name.strip().strip('"\'') for name in array_content.split(',')]
                return [name for name in names if name and name.strip()]
            
            # 尝试提取引号包围的企业名称
            quoted_names = re.findall(r'["\']([^"\']+公司[^"\']*|[^"\']+集团[^"\']*|[^"\']+股份[^"\']*|[^"\']+有限[^"\']*|[^"\']+企业[^"\']*)["\']', response)
            if quoted_names:
                return [name.strip() for name in quoted_names if name and name.strip()]
            
            # 尝试提取以"企业名称"开头的行
            lines = response.split('\n')
            company_names = []
            for line in lines:
                if line.strip().startswith('企业名称') or line.strip().startswith('-') or line.strip().startswith('*'):
                    # 提取冒号或破折号后的内容
                    name = re.sub(r'^[^:：]*[：:]?\s*[-*]?\s*', '', line.strip())
                    if name and name.strip():
                        company_names.append(name.strip())
            
            if company_names:
                return company_names
            
            # 如果都没有找到，尝试从整个响应中提取
            # 查找包含企业关键词的短语
            company_keywords = ['公司', '集团', '股份', '有限', '企业', '厂', '院', '所', '中心']
            found_names = []
            
            for keyword in company_keywords:
                # 查找关键词周围的文本
                matches = re.finditer(rf'[^，。！？\n\r]*{keyword}[^，。！？\n\r]*', response)
                for match in matches:
                    name = match.group().strip()
                    if len(name) >= 4 and len(name) <= 50:  # 合理的名称长度
                        found_names.append(name)
            
            return list(set(found_names))  # 去重
            
        except Exception as e:
            logger.error(f"解析企业名称响应失败: {str(e)}")
            return []
    
    def _deduplicate_companies(self, company_names: List[str]) -> List[CompanyName]:
        """去重和清理企业名称"""
        if not company_names:
            return []
        
        # 清理和标准化名称
        cleaned_names = []
        for name in company_names:
            # 去除多余的空白字符
            cleaned = re.sub(r'\s+', ' ', name.strip())
            # 去除常见的无关字符
            cleaned = re.sub(r'^[^a-zA-Z\u4e00-\u9fa5]*', '', cleaned)
            cleaned = re.sub(r'[^a-zA-Z\u4e00-\u9fa5]*$', '', cleaned)
            
            if cleaned and len(cleaned) >= 2:
                cleaned_names.append(cleaned)
        
        # 去重
        unique_names = []
        seen_names = set()
        
        for name in cleaned_names:
            # 检查是否已经存在相似名称
            is_duplicate = False
            for existing in seen_names:
                if self._is_similar_company_name(name, existing):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_names.append(CompanyName(name=name))
                seen_names.add(name)
        
        return unique_names
    
    def _is_similar_company_name(self, name1: str, name2: str) -> bool:
        """检查两个企业名称是否相似（可能是同一家公司的不同表述）"""
        # 如果两个名称完全相同，直接返回True
        if name1 == name2:
            return True
        
        # 如果两个名称长度差异很大，不太可能相似
        if abs(len(name1) - len(name2)) > 10:
            return False
        
        # 检查是否包含相同的核心词汇
        core_words1 = set(re.findall(r'[a-zA-Z\u4e00-\u9fa5]+', name1.lower()))
        core_words2 = set(re.findall(r'[a-zA-Z\u4e00-\u9fa5]+', name2.lower()))
        
        # 计算词汇相似度
        if core_words1 and core_words2:
            intersection = core_words1 & core_words2
            union = core_words1 | core_words2
            similarity = len(intersection) / len(union) if union else 0
            
            # 如果相似度超过60%，认为是相似名称
            if similarity > 0.6:
                return True
        
        # 检查是否一个名称是另一个名称的子串
        if name1 in name2 or name2 in name1:
            return True
        
        return False
    
    def _fallback_rule_based_extraction(self, text: str) -> List[CompanyName]:
        """备选方案：使用规则匹配提取企业名称"""
        logger.info("使用规则匹配作为备选方案")
        
        # 简化的企业名称关键词
        company_keywords = [
            '集团', '公司', '企业', '股份', '有限', '科技', '投资', '建设', 
            '发展', '管理', '咨询', '服务', '制造', '贸易', '实业', '环保', 
            '能源', '金融', '银行', '保险', '证券', '基金', '信托'
        ]
        
        company_names = []
        
        # 使用关键词匹配
        for keyword in company_keywords:
            if keyword in text:
                # 找到关键词位置
                pos = text.find(keyword)
                # 提取上下文
                start = max(0, pos - 30)
                end = min(len(text), pos + 30)
                context = text[start:end]
                
                # 尝试提取完整的企业名称
                company_name = self._extract_full_company_name_fallback(context, keyword)
                if company_name and company_name not in [c.name for c in company_names]:
                    company_names.append(CompanyName(name=company_name))
        
        return company_names
    
    def _extract_full_company_name_fallback(self, context: str, keyword: str) -> str:
        """备选方案的企业名称提取"""
        # 简单的企业名称提取逻辑
        start_pos = context.find(keyword)
        if start_pos == -1:
            return keyword
        
        # 向后扩展，寻找可能的名称后缀
        end_pos = start_pos + len(keyword)
        suffixes = ['公司', '集团', '股份', '有限', '责任', '企业', '厂', '院', '所', '中心']
        for suffix in suffixes:
            if suffix in context[end_pos:end_pos + 20]:
                end_pos = context.find(suffix, end_pos) + len(suffix)
                break
        
        # 向前扩展，寻找可能的名称前缀
        prefixes = ['中原', '郑州', '河南', '中国', '国家', '省级', '市级']
        for prefix in prefixes:
            if prefix in context[max(0, start_pos - 20):start_pos]:
                prefix_pos = context.rfind(prefix, 0, start_pos)
                if prefix_pos != -1:
                    start_pos = prefix_pos
                    break
        
        company_name = context[start_pos:end_pos].strip()
        
        # 清理名称
        company_name = company_name.replace('\n', '').replace('\t', ' ')
        company_name = ' '.join(company_name.split())
        
        return company_name if company_name else keyword 