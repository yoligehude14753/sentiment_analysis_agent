import requests
import json
import time
from typing import Dict, List, Optional
from config import Config

class AliLLMClient:
    def __init__(self):
        self.api_key = Config.get_ali_api_key()
        self.model_name = Config.ALI_MODEL_NAME
        self.base_url = Config.ALI_BASE_URL
        
    def generate_summary(self, content: str) -> str:
        """
        生成文本摘要
        要求：简洁明了，突出核心信息，100字以内
        """
        prompt = f"""
        请为以下文本生成一个简洁的摘要，要求：
        1. 突出核心信息和关键事件
        2. 语言简洁明了
        3. 控制在100字以内
        4. 保持客观中立
        
        文本内容：
        {content}
        
        摘要：
        """
        
        try:
            response = self._call_api(prompt)
            return response.strip()
        except Exception as e:
            return f"摘要生成失败: {str(e)}"
    
    def extract_companies(self, content: str):
        """
        识别文本中涉及的企业
        返回企业名称列表
        """
        from models import CompanyInfo
        
        prompt = f"""
        请从以下文本中识别涉及的企业、公司、机构等实体，要求：
        1. 提取所有企业名称、公司名称、机构名称
        2. 包括政府机构、事业单位、企业等
        3. 只返回企业名称，用逗号分隔
        4. 如果文本中没有涉及企业，返回"无"
        
        文本内容：
        {content}
        
        涉及企业：
        """
        
        try:
            response = self._call_api(prompt)
            if "无" in response or "没有" in response:
                return []
            
            # 解析企业名称列表
            company_names = [company.strip() for company in response.split(',') if company.strip()]
            
            # 为每个企业创建CompanyInfo对象
            companies = []
            for company_name in company_names:
                company_info = CompanyInfo(
                    name=company_name,
                    credit_code="",  # 暂时为空，后续可以扩展
                    reason=f"从文本中识别到企业名称：{company_name}"
                )
                companies.append(company_info)
            
            return companies
        except Exception as e:
            return [CompanyInfo(
                name="企业识别失败",
                credit_code="",
                reason=f"识别失败: {str(e)}"
            )]
    
    def generate_tags(self, content: str):
        """
        生成文本标签
        根据舆情分析的标准分类体系生成标签
        """
        from models import TagResult
        
        prompt = f"""
        请为以下文本生成标签，要求：
        1. 根据文本内容生成3-8个标签
        2. 标签应该涵盖：行业领域、事件类型、影响范围、关键主题等
        3. 标签要准确、具体、有区分度
        4. 用逗号分隔，不要重复
        
        文本内容：
        {content}
        
        标签：
        """
        
        try:
            response = self._call_api(prompt)
            # 解析标签列表
            tag_names = [tag.strip() for tag in response.split(',') if tag.strip()]
            
            # 为每个标签创建TagResult对象
            tags = []
            for tag_name in tag_names:
                tag_result = TagResult(
                    tag=tag_name,
                    belongs=True,
                    reason=f"文本内容与'{tag_name}'标签相关"
                )
                tags.append(tag_result)
            
            return tags
        except Exception as e:
            return [TagResult(
                tag="标签生成失败",
                belongs=False,
                reason=f"生成失败: {str(e)}"
            )]
    
    def analyze_sentiment_level(self, content: str):
        """
        分析情感等级
        根据舆情分析的标准情感分类体系
        """
        from models import SentimentResult
        
        prompt = f"""
        请分析以下文本的情感等级，要求：
        1. 情感等级：极低/低/中/高/极高
        2. 返回JSON格式结果
        
        文本内容：
        {content}
        
        请返回JSON格式：
        {{
            "level": "高",
            "reason": "简要分析原因"
        }}
        """
        
        try:
            response = self._call_api(prompt)
            result = self._parse_sentiment_response(response)
            return SentimentResult(
                level=result.get("level", "中"),
                reason=result.get("reason", "分析完成")
            )
        except Exception as e:
            return SentimentResult(
                level="中",
                reason=f"分析失败: {str(e)}"
            )
    
    def analyze_sentiment(self, content: str) -> Dict:
        """兼容旧版本的情感分析接口"""
        return self.analyze_sentiment_level(content)
    
    def extract_topics(self, content: str) -> List[str]:
        """兼容旧版本的主题提取接口"""
        return self.generate_tags(content)
    
    def summarize_content(self, content: str) -> str:
        """兼容旧版本的摘要生成接口"""
        return self.generate_summary(content)
    
    def _call_api(self, prompt: str) -> str:
        """调用阿里云通义千问API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 阿里云通义千问API请求格式
        data = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,  # 降低随机性，提高一致性
            "max_tokens": 1000
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            print(f"API响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                # 阿里云通义千问的响应格式
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                elif "output" in result and "text" in result["output"]:
                    return result["output"]["text"]
                else:
                    print(f"响应格式: {result}")
                    return str(result)
            else:
                raise Exception(f"API调用失败: {response.status_code} - {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"请求异常: {e}")
            raise Exception(f"网络请求失败: {str(e)}")
        except Exception as e:
            print(f"其他异常: {e}")
            raise Exception(f"API调用异常: {str(e)}")
    
    def _parse_sentiment_response(self, response: str) -> Dict:
        """解析情感分析响应"""
        try:
            # 尝试解析JSON
            if response.strip().startswith('{'):
                result = json.loads(response)
                # 只返回我们需要的字段
                return {
                    "level": result.get("level", "中"),
                    "reason": result.get("reason", "分析完成")
                }
            else:
                # 如果不是JSON格式，尝试提取关键信息
                return {
                    "level": "中",
                    "reason": response
                }
        except json.JSONDecodeError:
            return {
                "level": "中",
                "reason": response
            }
    
    def _parse_response(self, response: str) -> Dict:
        """兼容旧版本的响应解析"""
        return self._parse_sentiment_response(response)
    
    async def call_llm(self, system_prompt: str, user_message: str) -> Dict:
        """
        调用LLM进行对话
        用于聊天API的异步调用
        """
        try:
            # 构建完整的提示词
            full_prompt = f"{system_prompt}\n\n用户问题：{user_message}"
            
            # 调用API
            response = self._call_api(full_prompt)
            
            return {
                "success": True,
                "response": response
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            } 