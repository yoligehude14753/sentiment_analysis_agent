from typing import List, Optional
import inspect
from pydantic import BaseModel
import re
from models import SentimentResult
from config import Config
import logging
import json
from agents.ali_llm_client import AliLLMClient

logger = logging.getLogger(__name__)

class SentimentAgent:
    """情感分析Agent，专门负责5个情感等级的分类判断"""
    
    def __init__(self):
        # 初始化LLM客户端
        self.llm_client = AliLLMClient()
        self.prompt_template = Config.AGENT_PROMPTS.get("情感分析", Config.SENTIMENT_PROMPT_TEMPLATE)
        
        # 定义5个情感等级及其对应的识别规则
        self.sentiment_levels = {
            "负面三级（重大风险）": {
                "keywords": ["财务造假", "欺诈发行", "重大贿赂", "立案调查", "刑事处罚", "持续经营能力丧失", "核心业务停顿", "关键资质吊销", "核心技术丧失", "专利权属丧失", "重大诉讼", "控制权重大不确定性", "实际控制人纠纷", "股权冻结", "质押平仓", "控制权变更", "财务真实性崩塌", "虚增收入", "虚增利润", "体外资金循环"],
                "strong_signals": ["证监会", "公安", "立案调查", "刑事处罚", "资质吊销", "控制权变更", "虚增收入", "虚增利润"],
                "description": "可能导致IPO项目'一票否决'的致命风险，涉及严重违法犯罪、持续经营能力丧失、控制权重大不确定性、财务真实性崩塌等"
            },
            "负面二级（显著风险）": {
                "keywords": ["行政处罚", "税务", "环保", "产品质量", "劳动保障", "经营指标异常", "财务指标异常", "毛利率", "同行业", "单一客户", "供应商依赖", "重大诉讼", "仲裁", "知识产权", "关键合同", "关联交易", "定价公允", "商业合理性", "利益输送", "个人卡收付款", "资金占用", "内控缺陷"],
                "strong_signals": ["行政处罚", "指标异常", "重大诉讼", "关联交易", "个人卡收付款", "资金占用"],
                "description": "需要立即启动专项核查的风险点，涉及一般性违法违规、经营/财务指标重大异常、重大诉讼/仲裁、关联交易问题、内部控制严重缺陷等"
            },
            "负面一级（潜在风险/关注点）": {
                "keywords": ["市场传闻", "质疑", "业绩下滑", "客户变化", "供应商变化", "核心人员离职", "行业风险", "政策变化", "技术迭代", "市场环境", "并购重组", "估值", "条款", "分歧", "不确定性"],
                "strong_signals": ["市场传闻", "业绩下滑", "核心人员离职", "行业风险", "并购重组"],
                "description": "投行项目早期的预警信号和潜在关注点，涉及市场传闻与质疑、客观经营波动、行业性风险、交易不确定性等"
            },
            "中性": {
                "keywords": ["日常经营", "客观", "事实性", "常规", "正常", "发布", "签署", "合同", "人事变动", "信息披露", "行业报告", "提及"],
                "strong_signals": ["日常经营", "客观", "事实性"],
                "description": "对主体日常经营活动的客观、事实性报道，对项目风险评估无直接实质性影响"
            },
            "正面": {
                "keywords": ["技术突破", "产品认证", "权威机构", "重要奖项", "国家级", "国际级", "战略合作", "行业巨头", "经营业绩", "超预期", "市场认可", "声誉提升", "市场地位", "投资者信心"],
                "strong_signals": ["技术突破", "产品认证", "重要奖项", "战略合作", "超预期"],
                "description": "能提升公司价值和市场信心的信息，涉及重大技术突破、核心产品认证、重要奖项、重大战略合作、经营业绩超预期等"
            }
        }
    
    async def analyze_sentiment(self, content: str) -> SentimentResult:
        """
        分析文本的情感等级
        
        Args:
            content: 文本内容
            
        Returns:
            情感分析结果
        """
        try:
            # 使用最新运行时提示词（允许配置热更新），并安全插入内容
            runtime_prompt = Config.AGENT_PROMPTS.get("情感分析", self.prompt_template)
            template = runtime_prompt or Config.SENTIMENT_PROMPT_TEMPLATE
            prompt = self._fill_content_into_template(template, content)
            
            # 调用LLM获取分析结果，兼容同步/异步实现
            generated = self.llm_client.generate_response(prompt)
            if inspect.isawaitable(generated):
                response = await generated
            else:
                response = generated
            logger.debug(f"LLM情感分析原始响应: {response}")
            
            # 解析LLM响应
            return self._parse_llm_response(response, content)
        except Exception as e:
            logger.error(f"LLM情感分析失败: {str(e)}")
            # 出错时使用规则匹配作为备选方案
            return self._rule_based_analysis(content)

    def _fill_content_into_template(self, template: str, content: str) -> str:
        """将内容安全地填充到模板中，避免str.format对花括号的误解析。

        支持以下占位符：
        - {content}
        - {{content}}
        若模板未包含占位符，则在末尾追加“文本内容：\n{content}”。
        """
        try:
            if template is None:
                return content

            # 优先替换双花括号占位符
            if "{{content}}" in template:
                return template.replace("{{content}}", content)

            # 再处理单花括号占位符（不触发format机制）
            if "{content}" in template:
                return template.replace("{content}", content)

            # 未包含占位符则直接在末尾附加内容
            return f"{template}\n\n文本内容：\n{content}"
        except Exception:
            # 任何异常下，兜底返回简单拼接
            return f"{template}\n\n{content}"
    
    def _parse_llm_response(self, response: str, original_text: str) -> SentimentResult:
        """解析LLM的响应，提取情感等级和分析原因"""
        try:
            # 提取情感等级
            sentiment_match = re.search(r"情感等级[：:]\s*([^\n]+)", response)
            sentiment_level = sentiment_match.group(1).strip() if sentiment_match else "中性"
            
            # 标准化情感等级
            if "负面三级" in sentiment_level:
                sentiment_level = "负面三级（重大风险）"
            elif "负面二级" in sentiment_level:
                sentiment_level = "负面二级（显著风险）"
            elif "负面一级" in sentiment_level:
                sentiment_level = "负面一级（潜在风险/关注点）"
            elif "中性" in sentiment_level:
                sentiment_level = "中性"
            elif "正面" in sentiment_level:
                sentiment_level = "正面"
            
            # 提取分析原因
            reason_match = re.search(r"分析原因[：:]\s*([\s\S]+)", response)
            reason = reason_match.group(1).strip() if reason_match else "无详细分析"
            
            return SentimentResult(
                level=sentiment_level,
                reason=reason
            )
        except Exception as e:
            logger.error(f"解析LLM情感分析响应失败: {str(e)}")
            # 解析失败时使用规则匹配作为备选方案
            return self._rule_based_analysis(original_text)
    
    def _rule_based_analysis(self, content: str) -> SentimentResult:
        """使用规则匹配进行情感分析（作为备选方案）"""
        # 分析每个情感等级
        level_scores = {}
        
        for level_name, level_rule in self.sentiment_levels.items():
            score = self._calculate_level_score(content, level_rule)
            level_scores[level_name] = score
        
        # 选择得分最高的情感等级
        best_level = max(level_scores.items(), key=lambda x: x[1])
        
        # 生成原因说明
        reason = self._generate_sentiment_reason(content, best_level[0], best_level[1])
        
        return SentimentResult(
            level=best_level[0],
            reason=reason
        )
    
    def _calculate_level_score(self, content: str, level_rule: dict) -> float:
        """计算某个情感等级的得分"""
        score = 0.0
        
        # 关键词匹配得分
        keyword_matches = []
        for keyword in level_rule["keywords"]:
            if keyword in content:
                keyword_matches.append(keyword)
                score += 1.0
        
        # 强信号匹配得分（权重更高）
        strong_signal_matches = []
        for signal in level_rule["strong_signals"]:
            if signal in content:
                strong_signal_matches.append(signal)
                score += 2.0  # 强信号权重更高
        
        # 上下文分析得分
        context_score = self._analyze_context_score(content, level_rule)
        score += context_score
        
        return score
    
    def _analyze_context_score(self, content: str, level_rule: dict) -> float:
        """分析上下文得分"""
        context_score = 0.0
        
        # 检查是否有相关的负面词汇组合（基于情感等级名称判断）
        level_name = list(self.sentiment_levels.keys())[list(self.sentiment_levels.values()).index(level_rule)]
        if "负面" in level_name:  # 负面情感
            negative_combinations = [
                ["处罚", "违规", "违法"],
                ["问题", "风险", "危机"],
                ["下降", "减少", "降低"],
                ["质疑", "怀疑", "不确定"],
                ["纠纷", "争议", "冲突"]
            ]
            
            for combo in negative_combinations:
                if all(word in content for word in combo):
                    context_score += 1.0
        
        # 检查是否有相关的正面词汇组合
        elif "正面" in level_name or "中性" in level_name:  # 正面或中性情感
            positive_combinations = [
                ["增长", "提升", "改善"],
                ["成功", "突破", "创新"],
                ["合作", "签约", "协议"],
                ["认证", "认可", "好评"],
                ["稳定", "正常", "良好"]
            ]
            
            for combo in positive_combinations:
                if all(word in content for word in combo):
                    context_score += 1.0
        
        return context_score
    
    def _generate_sentiment_reason(self, content: str, level: str, score: float) -> str:
        """生成情感分析原因说明"""
        level_rule = self.sentiment_levels[level]
        reasons = []
        
        # 添加情感等级描述
        reasons.append(f"判定为{level}: {level_rule['description']}")
        
        # 添加关键词匹配信息
        keyword_matches = []
        for keyword in level_rule["keywords"]:
            if keyword in content:
                keyword_matches.append(keyword)
        
        if keyword_matches:
            reasons.append(f"检测到相关关键词: {', '.join(keyword_matches[:5])}")  # 最多显示5个
        
        # 添加强信号匹配信息
        strong_signal_matches = []
        for signal in level_rule["strong_signals"]:
            if signal in content:
                strong_signal_matches.append(signal)
        
        if strong_signal_matches:
            reasons.append(f"检测到强信号: {', '.join(strong_signal_matches)}")
        
        # 添加得分信息
        reasons.append(f"综合评分: {score:.2f}")
        
        # 添加相关上下文
        context = self._find_relevant_context(content, level_rule["keywords"])
        if context:
            reasons.append(f"相关上下文: {context}")
        
        return "；".join(reasons)
    
    def _find_relevant_context(self, content: str, keywords: List[str]) -> str:
        """查找关键词相关的上下文"""
        for keyword in keywords:
            if keyword in content:
                pos = content.find(keyword)
                start = max(0, pos - 100)
                end = min(len(content), pos + len(keyword) + 100)
                context = content[start:end].strip()
                if len(context) > 50:
                    return context[:200] + "..." if len(context) > 200 else context
        return ""
    
    async def get_sentiment_summary(self, content: str) -> dict:
        """获取情感分析摘要"""
        try:
            # 使用LLM进行情感分析
            result = await self.analyze_sentiment(content)
            
            # 返回摘要
            return {
                "primary_sentiment": result.level,
                "reason": result.reason,
                "method": "llm"
            }
        except Exception as e:
            logger.error(f"获取情感分析摘要失败: {str(e)}")
            
            # 备选方案：使用规则匹配
            # 分析所有情感等级的得分
            level_scores = {}
            for level_name, level_rule in self.sentiment_levels.items():
                score = self._calculate_level_score(content, level_rule)
                level_scores[level_name] = score
            
            # 按得分排序
            sorted_levels = sorted(level_scores.items(), key=lambda x: x[1], reverse=True)
            
            return {
                "primary_sentiment": sorted_levels[0][0],
                "primary_score": sorted_levels[0][1],
                "all_scores": level_scores,
                "sorted_levels": sorted_levels,
                "method": "rule_based"
            } 