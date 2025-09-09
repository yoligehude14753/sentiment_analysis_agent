from typing import List
import inspect
import logging
from models import TagResult
from agents.ali_llm_client import AliLLMClient
from config import Config

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TagAgent:
    """单个标签分析Agent"""

    def __init__(self, tag_name: str, description: str, llm_client: AliLLMClient, custom_prompt: str = None):
        self.tag_name = tag_name
        self.description = description
        self.llm_client = llm_client
        self.custom_prompt = custom_prompt
    
    async def analyze(self, content: str) -> TagResult:
        """
        分析文本是否属于该标签
        
        Args:
            content: 文本内容
            
        Returns:
            标签分析结果
        """
        try:
            # 构建专业的分析提示词
            prompt = self._build_analysis_prompt(content)
            
            # 调用LLM进行分析，兼容同步/异步客户端
            generated = self.llm_client.generate_response(prompt)
            if inspect.isawaitable(generated):
                response = await generated
            else:
                response = generated
            
            # 解析LLM响应
            belongs, reason = self._parse_llm_response(response)
            
            return TagResult(
                tag=self.tag_name,
                belongs=belongs,
                reason=reason
            )
            
        except Exception as e:
            logger.error(f"标签 {self.tag_name} 分析失败: {str(e)}")
            return TagResult(
                tag=self.tag_name,
                belongs=False,
                reason=f"分析失败: {str(e)}"
            )
    
    def _build_analysis_prompt(self, content: str) -> str:
        """构建专业的分析提示词（支持运行时模板）"""
        # 优先使用自定义提示词
        if self.custom_prompt and self.custom_prompt.strip():
            template = self.custom_prompt
        else:
            # 回退到全局模板
            template = Config.TAG_PROMPT_TEMPLATE or ""

        if template:
            try:
                return self._fill_content_into_template(template, content)
            except Exception:
                pass

        # 兜底：使用内置模板
        return f"你是一个专业的IPO风险评估专家，专门负责分析新闻文本是否涉及\"{self.tag_name}\"风险。\n\n标签定义：{self.description}\n\n请仔细分析以下新闻文本，判断是否涉及\"{self.tag_name}\"风险：\n\n{content}\n\n分析要求：\n1. 仔细阅读文本内容，理解事件背景和具体情况\n2. 根据标签定义，判断文本是否涉及该风险\n3. 如果涉及，请详细说明判断依据和风险点\n4. 如果不涉及，请说明原因\n\n请按照以下格式返回分析结果：\n\n判断结果：[是/否]\n分析原因：[详细的分析说明，包括具体的风险点或判断依据]\n\n注意：\n- 判断要客观、准确，基于文本内容而非主观臆测\n- 分析原因要具体、有说服力\n- 如果涉及风险，要明确指出具体的风险点\n- 如果不涉及，要说明为什么不符合该标签特征"

    def _fill_content_into_template(self, template: str, content: str) -> str:
        """将内容安全地填充到模板中，避免str.format对花括号的误解析。
        
        支持以下占位符：
        - {content}
        - {{content}}
        - {tag_name}
        - {description}
        若模板未包含占位符，则在末尾追加"文本内容：\n{content}"。
        """
        try:
            if template is None:
                return content

            # 优先替换双花括号占位符
            if "{{content}}" in template:
                template = template.replace("{{content}}", content)
            if "{{tag_name}}" in template:
                template = template.replace("{{tag_name}}", self.tag_name)
            if "{{description}}" in template:
                template = template.replace("{{description}}", self.description)

            # 再处理单花括号占位符（不触发format机制）
            if "{content}" in template:
                template = template.replace("{content}", content)
            if "{tag_name}" in template:
                template = template.replace("{tag_name}", self.tag_name)
            if "{description}" in template:
                template = template.replace("{description}", self.description)

            # 未包含占位符则直接在末尾附加内容
            return f"{template}\n\n文本内容：\n{content}"
        except Exception:
            # 任何异常下，兜底返回简单拼接
            return f"{template}\n\n{content}"
    
    def _parse_llm_response(self, response: str) -> tuple:
        """解析LLM的响应"""
        try:
            response = response.strip()
            
            # 检查是否包含判断结果
            if "判断结果：是" in response or "是" in response[:20]:
                belongs = True
            elif "判断结果：否" in response or "否" in response[:20]:
                belongs = False
            else:
                # 如果没有明确的判断结果，尝试从内容推断
                belongs = "风险" in response or "问题" in response or "违规" in response
            
            # 提取分析原因
            if "分析原因：" in response:
                reason = response.split("分析原因：")[-1].strip()
            else:
                reason = response.strip()
            
            # 如果原因太短，使用完整响应
            if len(reason) < 10:
                reason = response.strip()
            
            return belongs, reason
            
        except Exception as e:
            logger.error(f"解析LLM响应失败: {str(e)}")
            return False, f"响应解析失败: {str(e)}"

class TagAgents:
    """标签分类Agents，包含14个专门的标签识别agent"""
    
    def __init__(self):
        # 初始化LLM客户端
        self.llm_client = AliLLMClient()
        
        # 定义14个标签及其描述
        self.tag_definitions = {
            # 公司治理与合规风险
            "同业竞争": "发行人的独立性受到损害，控股股东、实际控制人或其近亲属所控制的其他企业与发行人从事相同或高度相似的业务，存在利益冲突、利润转移等风险",
            
            "股权与控制权": "股权结构不稳定，控制权不清晰，存在大规模质押、司法冻结、查封、控制权变更等风险",
            
            "关联交易": "可能损害公司利益的关联交易，定价不公允，存在利益输送或调节利润，关联方注销、转让等非关联化操作",
            
            "历史沿革与股东核查": "历史沿革和股东结构中的合规瑕疵，存在股权代持、突击入股、三类股东（契约型基金、资管计划、信托计划）等问题",
            
            "重大违法违规": "公司或其关键人物的重大违法违规行为，受到行政处罚或刑事立案/处罚，涉及安全生产、环境保护、产品质量、税务、劳动社保、商业贿赂等",
            
            # 财务真实性与经营能力
            "收入与成本": "收入真实性、成本合理性存在质疑，毛利率异常，收入增长与经营状况不符，产能利用率、客户订单等支撑不足",
            
            "财务内控不规范": "财务内部控制的重大缺陷，个人卡收付款、资金被占用、账外账、体外资金循环、粉饰业绩等",
            
            "客户与供应商": "客户与供应商结构中的潜在风险，高度集中（前五大客户/供应商占比过高）、背景异常、注册资本异常、前员工身份重叠等",
            
            "资产质量与减值": "资产质量存在问题，应收账款逾期、存货积压、商誉减值风险，坏账准备、跌价准备计提不足等",
            
            "研发与技术": "技术风险与研发投入的合规性，会计处理不合规、技术权属纠纷、技术来源不稳定（授权、购买而非自主研发）等",
            
            # 发行与市场风险
            "募集资金用途": "募集资金用途的合理性存疑，与主业无关、必要性存疑、主要用于补充流动资金或偿还银行贷款等",
            
            "突击分红与对赌协议": "IPO申报前夕的大额现金分红，未清理的对赌协议，估值调整机制、市值挂钩等影响估值或股权稳定性的条款",
            
            "市场传闻与负面报道": "已形成较大市场影响力的负面舆情事件，传播广度和市场影响显著，媒体报道、舆论热点等",
            
            "行业政策与环境": "对发行人构成系统性风险的外部环境变化，政策风险、市场风险、外部冲击，产业政策调整、监管收紧、技术颠覆等"
        }
        
        # 创建14个专门的标签分析agent
        self.tag_agents = {}
        for tag_name, description in self.tag_definitions.items():
            # 获取该标签的自定义提示词
            custom_prompt = Config.AGENT_PROMPTS.get(tag_name)
            self.tag_agents[tag_name] = TagAgent(tag_name, description, self.llm_client, custom_prompt)
        
        logger.info(f"标签分析系统初始化完成，共创建 {len(self.tag_agents)} 个标签分析agent")
    
    async def analyze_tags(self, content: str) -> List[TagResult]:
        """
        使用14个专门的agent分析文本中的所有标签
        
        Args:
            content: 文本内容
            
        Returns:
            标签分析结果列表
        """
        logger.info(f"开始标签分析，文本长度: {len(content)}")
        results = []
        
        # 逐个调用每个标签分析agent
        for tag_name, agent in self.tag_agents.items():
            logger.info(f"正在分析标签: {tag_name}")
            
            try:
                # 调用专门的agent进行分析
                result = await agent.analyze(content)
                results.append(result)
                
                logger.info(f"标签 {tag_name} 分析完成: {'匹配' if result.belongs else '不匹配'}")
                
            except Exception as e:
                logger.error(f"标签 {tag_name} 分析异常: {str(e)}")
                # 创建错误结果
                results.append(TagResult(
                    tag=tag_name,
                    belongs=False,
                    reason=f"分析异常: {str(e)}"
                ))
        
        logger.info(f"标签分析完成，共分析 {len(results)} 个标签")
        return results
    
    def get_tag_summary(self, results: List[TagResult]) -> dict:
        """获取标签分析摘要"""
        positive_tags = [result.tag for result in results if result.belongs]
        negative_tags = [result.tag for result in results if not result.belongs]
        
        return {
            "total_tags": len(results),
            "positive_tags": positive_tags,
            "negative_tags": negative_tags,
            "positive_count": len(positive_tags),
            "negative_count": len(negative_tags)
        }
    
    async def analyze_single_tag(self, content: str, tag_name: str) -> TagResult:
        """
        分析单个标签（用于调试或特定需求）

        Args:
            content: 文本内容
            tag_name: 标签名称

        Returns:
            标签分析结果
        """
        if tag_name not in self.tag_agents:
            return TagResult(
                tag=tag_name,
                belongs=False,
                reason=f"标签 {tag_name} 不存在"
            )

        return await self.tag_agents[tag_name].analyze(content)

    def update_agent_prompt(self, tag_name: str, custom_prompt: str) -> bool:
        """
        更新单个Agent的提示词

        Args:
            tag_name: 标签名称
            custom_prompt: 新的提示词模板

        Returns:
            更新是否成功
        """
        if tag_name not in self.tag_agents:
            return False

        # 更新Agent的提示词
        self.tag_agents[tag_name].custom_prompt = custom_prompt

        # 更新配置
        Config.AGENT_PROMPTS[tag_name] = custom_prompt

        logger.info(f"更新Agent {tag_name} 的提示词成功")
        return True

    def get_agent_prompt(self, tag_name: str) -> str:
        """
        获取单个Agent的提示词

        Args:
            tag_name: 标签名称

        Returns:
            当前使用的提示词
        """
        if tag_name not in self.tag_agents:
            return ""

        agent = self.tag_agents[tag_name]
        return agent.custom_prompt or Config.TAG_PROMPT_TEMPLATE

    def get_all_agent_prompts(self) -> dict:
        """
        获取所有Agent的提示词

        Returns:
            包含所有Agent提示词的字典
        """
        return {tag_name: self.get_agent_prompt(tag_name) for tag_name in self.tag_agents.keys()} 