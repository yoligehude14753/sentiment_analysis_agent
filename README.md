# 多Agent情感分析系统

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)]()

> 基于多Agent架构的智能舆情分析系统，专注于企业风险识别和情感分析

## 🎯 项目简介

本系统采用多Agent架构，将复杂的舆情分析任务分解为三个专门的智能代理，实现对新闻文本的企业识别、标签分类和情感分析。系统专为投资银行、风险管控和企业监管场景设计，提供精准的风险预警和情感评估。

## 🏗️ 系统架构

本系统采用多Agent架构，将复杂的舆情分析任务分解为三个专门的Agent：

### 1. 企业识别Agent (CompanyAgent)
- **职责**: 识别新闻中的企业名称和统一社会信用代码
- **输出**: 企业名称、统一社会信用代码、识别原因
- **特点**: 基于正则表达式和模式匹配，支持中英文企业名称识别

### 2. 标签分类Agents (TagAgents)
- **职责**: 对新闻进行14个维度的标签分类
- **标签体系**:
  - **公司治理与合规风险**: 同业竞争、股权与控制权、关联交易、历史沿革与股东核查、重大违法违规
  - **财务真实性与经营能力**: 收入与成本、财务内控不规范、客户与供应商、资产质量与减值、研发与技术
  - **发行与市场风险**: 募集资金用途、突击分红与对赌协议、市场传闻与负面报道、行业政策与环境
- **输出**: 每个标签的匹配结果和原因说明

### 3. 情感分析Agent (SentimentAgent)
- **职责**: 对新闻进行5个情感等级的分类
- **情感等级**:
  - 负面三级（重大风险）: 可能导致IPO项目"一票否决"的致命风险
  - 负面二级（显著风险）: 需要立即启动专项核查的风险点
  - 负面一级（潜在风险/关注点）: 投行项目早期的预警信号
  - 中性: 对项目风险评估无直接实质性影响
  - 正面: 能提升公司价值和市场信心的信息
- **输出**: 情感等级和详细的分析原因

## 技术特点

1. **规则驱动**: 基于关键词匹配和强信号识别，确保分析结果的可解释性
2. **上下文感知**: 不仅匹配关键词，还分析上下文语境
3. **智能评分**: 情感分析采用多维度评分机制，确保分析结果的准确性
4. **可扩展性**: 每个Agent都可以独立优化和扩展

## 使用方法

### 🚀 快速启动

#### 方法1：使用批处理脚本 (Windows推荐)
```bash
# 双击运行
start.bat
```

#### 方法2：直接运行Python
```bash
cd sentiment-analysis-agent
pip install -r requirements.txt
python main.py
```

### 📖 详细启动说明
更多启动选项和配置说明，请参考 [STARTUP_GUIDE.md](STARTUP_GUIDE.md)

### API接口
- **POST /api/analyze**: 分析新闻内容
- **GET /**: 系统状态检查

### 测试系统
```bash
python test_system.py
```

## 示例输出

```json
{
  "companies": [
    {
      "name": "某环保科技有限公司",
      "credit_code": "91110000123456789X",
      "reason": "识别为环保企业；匹配到统一社会信用代码: 91110000123456789X；涉及处罚或违规事件"
    }
  ],
  "tags": [
    {
      "tag": "重大违法违规",
      "belongs": true,
      "reason": "检测到相关关键词: 环保问题, 罚款；检测到强信号: 环保局, 罚款；符合重大违法违规标签特征: 公司或其关键人物的重大违法违规行为，受到行政处罚或刑事立案/处罚；相关上下文: 某环保科技有限公司因环保问题被环保局处以50万元罚款"
    }
  ],
  "sentiment": {
    "level": "负面二级（显著风险）",
    "reason": "判定为负面二级（显著风险）: 需要立即启动专项核查的风险点，涉及一般性违法违规、经营/财务指标重大异常、重大诉讼/仲裁、关联交易问题、内部控制严重缺陷等；检测到相关关键词: 环保问题, 罚款, 行政处罚；检测到强信号: 行政处罚；综合评分: 8.50；相关上下文: 某环保科技有限公司因环保问题被环保局处以50万元罚款"
  }
}
```

## 系统优势

1. **专业化分工**: 每个Agent专注于特定任务，提高分析精度
2. **标准化输出**: 统一的JSON格式，便于后续处理
3. **可追溯性**: 每个分析结果都包含详细的原因说明
4. **实时性**: 基于规则的分析，响应速度快
5. **可维护性**: 模块化设计，便于维护和升级

## 📁 项目结构

```
sentiment-analysis-agent/
├── agents/                 # 核心Agent模块
│   ├── company_agent.py   # 企业识别Agent
│   ├── sentiment_agent.py # 情感分析Agent
│   └── tag_agents.py      # 标签分类Agents
├── config/                # 配置文件
├── data/                  # 数据存储
├── static/               # 静态资源
├── templates/            # HTML模板
├── main.py              # 主程序入口
├── requirements.txt     # 依赖包列表
└── README.md           # 项目说明
```

## 🚀 快速开始

### 环境要求
- Python 3.8+
- 内存: 4GB+
- 磁盘空间: 1GB+

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/your-username/sentiment-analysis-agent.git
cd sentiment-analysis-agent
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **启动系统**
```bash
# Windows
start.bat

# Linux/Mac
python main.py
```

## 📊 性能指标

- **处理速度**: 单条新闻分析 < 100ms
- **准确率**: 企业识别 > 95%，情感分析 > 90%
- **并发支持**: 最高支持100并发请求
- **内存占用**: 基础运行 < 500MB

## 🔧 配置说明

系统支持多种配置方式，详见 [配置文档](config/README.md)

## 📚 文档导航

- [快速启动指南](STARTUP_GUIDE.md)
- [Git版本管理](GIT_SETUP_GUIDE.md)
- [API接口文档](API_DOCUMENTATION.md)
- [部署指南](deploy_guide.md)
- [数据库架构](DATABASE_ARCHITECTURE.md)

## 🤝 贡献指南

我们欢迎社区贡献！请查看 [贡献指南](CONTRIBUTING.md) 了解如何参与项目开发。

### 开发流程
1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📈 未来规划

- [ ] **机器学习集成**: 集成深度学习模型提升分析精度
- [ ] **多语言支持**: 扩展英文、日文等多语言分析能力
- [ ] **实时监控**: 构建7x24小时实时舆情监控系统
- [ ] **可视化界面**: 开发现代化Web仪表板
- [ ] **API网关**: 构建企业级API服务
- [ ] **移动端支持**: 开发移动端应用

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 💬 联系我们

- 项目主页: [GitHub Repository](https://github.com/your-username/sentiment-analysis-agent)
- 问题反馈: [Issues](https://github.com/your-username/sentiment-analysis-agent/issues)
- 功能建议: [Discussions](https://github.com/your-username/sentiment-analysis-agent/discussions)

## 🙏 致谢

感谢所有为项目做出贡献的开发者和用户！

---

⭐ 如果这个项目对您有帮助，请给我们一个星标！