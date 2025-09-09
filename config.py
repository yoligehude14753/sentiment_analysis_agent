import os
from dotenv import load_dotenv

load_dotenv()

def _get_ali_api_key():
    """获取阿里云API密钥（延迟加载）"""
    try:
        from api_key_manager import api_key_manager
        return api_key_manager.get_api_key("dashscope")
    except ImportError:
        # 如果API密钥管理器不可用，回退到环境变量
        return os.getenv("DASHSCOPE_API_KEY")

class Config:
    # 阿里云通义千问API配置
    _ali_api_key = None
    
    @classmethod
    def get_ali_api_key(cls):
        """获取阿里云API密钥（延迟加载）"""
        if cls._ali_api_key is None:
            cls._ali_api_key = _get_ali_api_key()
        return cls._ali_api_key
    
    # 为了向后兼容，将ALI_API_KEY设为None，在首次访问时动态设置
    ALI_API_KEY = None
    ALI_MODEL_NAME = os.getenv("ALI_MODEL_NAME", "qwen-turbo")  # 使用qwen-turbo模型
    ALI_BASE_URL = os.getenv("ALI_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")  # 阿里云通义千问API端点
    
    # 服务器配置
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    
    # 数据文件路径
    DATA_FILE_PATH = "data/sentiment_data.csv"
    
    # 分析配置
    MAX_CONTENT_LENGTH = 2000  # 最大内容长度
    BATCH_SIZE = 100  # 批处理大小 

    # 提示词模板配置（可在配置页修改）
    TAG_PROMPT_TEMPLATE = (
        """
你是一个专业的IPO风险评估专家，专门负责分析新闻文本是否涉及"{tag_name}"风险。

标签定义：{description}

请仔细分析以下新闻文本，判断是否涉及"{tag_name}"风险：

{content}

分析要求：
1. 仔细阅读文本内容，理解事件背景和具体情况
2. 根据标签定义，判断文本是否涉及该风险
3. 如果涉及，请详细说明判断依据和风险点
4. 如果不涉及，请说明原因

请按照以下格式返回分析结果：

判断结果：[是/否]
分析原因：[详细的分析说明，包括具体的风险点或判断依据，字数不超过200字]

注意：
- 判断要客观、准确，基于文本内容而非主观臆测
- 分析原因要具体、有说服力，但字数必须控制在200字以内
- 如果涉及风险，要明确指出具体的风险点
- 如果不涉及，要说明为什么不符合该标签特征
- 请确保分析原因部分不超过200字
"""
    )

    # 情感分析提示词模板
    SENTIMENT_PROMPT_TEMPLATE = (
        """
你是一个专业的IPO风险评估专家，专门负责分析新闻文本的情感等级。

请仔细分析以下新闻文本，判断其情感等级：

{content}

情感等级定义：
1. 负面三级（重大风险）：可能导致IPO项目"一票否决"的致命风险，涉及严重违法犯罪、持续经营能力丧失、控制权重大不确定性、财务真实性崩塌等
2. 负面二级（显著风险）：需要立即启动专项核查的风险点，涉及一般性违法违规、经营/财务指标重大异常、重大诉讼/仲裁、关联交易问题、内部控制严重缺陷等
3. 负面一级（潜在风险/关注点）：投行项目早期的预警信号和潜在关注点，涉及市场传闻与质疑、客观经营波动、行业性风险、交易不确定性等
4. 中性：对主体日常经营活动的客观、事实性报道，对项目风险评估无直接实质性影响
5. 正面：能提升公司价值和市场信心的信息，涉及重大技术突破、核心产品认证、重要奖项、重大战略合作、经营业绩超预期等

分析要求：
1. 仔细阅读文本内容，理解事件背景和具体情况
2. 根据情感等级定义，判断文本的情感等级
3. 详细说明判断依据和关键点

请按照以下格式返回分析结果：

情感等级：[负面三级/负面二级/负面一级/中性/正面]
分析原因：[详细的分析说明，包括具体的判断依据，字数不超过200字]

注意：
- 判断要客观、准确，基于文本内容而非主观臆测
- 分析原因要具体、有说服力，但字数必须控制在200字以内
- 要明确指出支持判断的关键词或句子
- 请确保分析原因部分不超过200字
"""
    )

    # 企业识别提示词模板
    COMPANY_PROMPT_TEMPLATE = (
        """
你是一个专业的企业信息识别专家，专门负责从新闻文本中识别和归纳企业信息。

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
{content}
"""
    )

    # 每个Agent的独立提示词配置
    AGENT_PROMPTS = {
        # 情感分析
        "情感分析": os.getenv("PROMPT_情感分析", SENTIMENT_PROMPT_TEMPLATE),
        
        # 企业识别
        "企业识别": os.getenv("PROMPT_企业识别", COMPANY_PROMPT_TEMPLATE),
        
        # 公司治理与合规风险
        "同业竞争": os.getenv("PROMPT_同业竞争", TAG_PROMPT_TEMPLATE),
        "股权与控制权": os.getenv("PROMPT_股权与控制权", TAG_PROMPT_TEMPLATE),
        "关联交易": os.getenv("PROMPT_关联交易", TAG_PROMPT_TEMPLATE),
        "历史沿革与股东核查": os.getenv("PROMPT_历史沿革与股东核查", TAG_PROMPT_TEMPLATE),
        "重大违法违规": os.getenv("PROMPT_重大违法违规", TAG_PROMPT_TEMPLATE),

        # 财务真实性与经营能力
        "收入与成本": os.getenv("PROMPT_收入与成本", TAG_PROMPT_TEMPLATE),
        "财务内控不规范": os.getenv("PROMPT_财务内控不规范", TAG_PROMPT_TEMPLATE),
        "客户与供应商": os.getenv("PROMPT_客户与供应商", TAG_PROMPT_TEMPLATE),
        "资产质量与减值": os.getenv("PROMPT_资产质量与减值", TAG_PROMPT_TEMPLATE),
        "研发与技术": os.getenv("PROMPT_研发与技术", TAG_PROMPT_TEMPLATE),

        # 发行与市场风险
        "募集资金用途": os.getenv("PROMPT_募集资金用途", TAG_PROMPT_TEMPLATE),
        "突击分红与对赌协议": os.getenv("PROMPT_突击分红与对赌协议", TAG_PROMPT_TEMPLATE),
        "市场传闻与负面报道": os.getenv("PROMPT_市场传闻与负面报道", TAG_PROMPT_TEMPLATE),

        # 行业政策与环境
        "行业政策与环境": os.getenv("PROMPT_行业政策与环境", TAG_PROMPT_TEMPLATE),
    }