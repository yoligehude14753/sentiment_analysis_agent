# LLM企业识别功能实现说明

## 概述

本系统新增了基于LLM的企业识别功能，替代了原有的复杂企业识别逻辑，提供更智能、更准确的企业名称识别能力。

## 主要特性

### 1. 智能企业识别
- 使用阿里云通义千问LLM进行企业名称识别
- 能够识别各种形式的企业名称（全称、简称、英文名等）
- 自动去重和归一化处理

### 2. 提示词可配置
- 在Agent配置页面支持自定义企业识别提示词
- 可以根据业务需求调整识别规则和输出格式
- 支持实时保存和重置提示词

### 3. 简化输出格式
- 只返回企业名称，不包含复杂的元数据
- 输出格式：`CompanyInfo(name="企业名称")`
- 便于后续处理和展示

## 技术实现

### 1. 后端修改

#### 配置文件 (`config.py`)
```python
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
```

#### 企业识别代理 (`agents/company_agent.py`)
```python
class CompanyAgent:
    def __init__(self):
        self.llm_client = AliLLMClient()
        self.prompt_template = config.AGENT_PROMPTS.get("企业识别", config.COMPANY_PROMPT_TEMPLATE)
    
    async def analyze_companies(self, content: str) -> List[CompanyInfo]:
        """使用LLM识别企业名称"""
        prompt = self.prompt_template.format(content=content)
        
        try:
            response = await self.llm_client.chat_completion(prompt)
            company_names = self._parse_llm_response(response)
            
            # 转换为CompanyInfo对象
            companies = []
            for name in company_names:
                if name.strip():
                    companies.append(CompanyInfo(name=name.strip()))
            
            return companies
            
        except Exception as e:
            logger.error(f"企业识别失败: {e}")
            return []
```

### 2. 前端修改

#### 配置页面 (`templates/config.html`)
- 在情感分析提示词后面添加了企业识别提示词配置
- 支持展开/折叠、保存、重置等操作
- 与其他Agent提示词保持一致的UI风格

#### JavaScript配置 (`static/config.js`)
- 在`saveAllAgentPrompts`和`resetAllAgentPrompts`函数中添加"企业识别"
- 确保企业识别提示词能够被正确保存和重置

### 3. 主程序修改 (`main.py`)
```python
async def company_analysis():
    yield f"data: {json.dumps({'type': 'progress', 'step': 'companies', 'message': '正在识别企业信息...'})}\n\n"
    results = await company_agent.analyze_companies(request.content)
    # 现在企业识别只返回企业名称，转换为兼容格式
    company_data = [{"name": c.name, "credit_code": "", "reason": f"LLM智能识别: {c.name}"} for c in results]
    yield f"data: {json.dumps({'type': 'result', 'step': 'companies', 'data': company_data})}\n\n"
```

## 使用方法

### 1. 配置企业识别提示词
1. 访问Agent配置页面 (`/config`)
2. 找到"企业识别提示词"部分
3. 点击展开，修改提示词内容
4. 点击保存按钮

### 2. 测试企业识别功能
```bash
python test_company_llm.py
```

### 3. 在Web界面中使用
1. 访问主页面 (`/`)
2. 输入包含企业名称的文本
3. 点击"开始分析"
4. 查看企业识别结果

## 优势

### 1. 智能化程度高
- 能够理解上下文，准确识别企业名称
- 支持多种命名方式的自动归一化
- 减少误识别和漏识别

### 2. 维护成本低
- 无需维护复杂的规则库
- 提示词可配置，适应不同业务场景
- 统一的LLM接口，便于扩展

### 3. 用户体验好
- 识别结果更准确
- 支持实时配置调整
- 与其他Agent功能保持一致

## 注意事项

### 1. LLM依赖
- 需要配置有效的阿里云API密钥
- 依赖网络连接和API服务稳定性
- 响应时间可能比规则引擎稍长

### 2. 提示词优化
- 建议根据实际业务场景优化提示词
- 可以添加行业特定的识别规则
- 定期评估和调整识别效果

### 3. 成本控制
- 监控API调用次数和费用
- 考虑批量处理时的成本优化
- 设置合理的请求频率限制

## 未来扩展

### 1. 多模型支持
- 支持其他LLM提供商（如OpenAI、百度等）
- 实现模型自动切换和负载均衡
- 支持本地模型部署

### 2. 识别精度提升
- 添加企业名称验证和纠错
- 支持企业关系图谱构建
- 集成工商信息数据库

### 3. 性能优化
- 实现企业识别结果缓存
- 支持异步批量处理
- 优化提示词模板结构
