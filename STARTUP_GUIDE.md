# 🚀 舆情分析系统启动指南

## 📋 系统概述

本系统是一个基于FastAPI的多Agent舆情分析系统，支持：
- 单条文本情感分析
- 批量数据分析
- 企业识别和标签分类
- 数据库管理和结果导出

## 🎯 快速启动

### 方法1：使用批处理脚本 (Windows推荐)
```bash
# 双击运行
start.bat
```

### 方法2：直接运行Python
```bash
# 安装依赖
pip install -r requirements.txt

# 启动系统
python main.py
```

## 🌐 访问系统

启动成功后，在浏览器中访问：
- **主页**: http://localhost:8000
- **数据库管理**: http://localhost:8000/database
- **配置页面**: http://localhost:8000/config
- **结果数据库**: http://localhost:8000/results

## 📁 系统架构

```
sentiment-analysis-agent/
├── main.py              # 🚀 主应用入口
├── start.bat            # 🪟 Windows启动脚本
├── config/              # ⚙️ 配置文件
├── agents/              # 🤖 AI代理模块
├── static/              # 🎨 前端静态文件
├── templates/           # 📄 HTML模板
└── data/                # 💾 数据文件
```

## 🔧 配置说明

### 环境变量配置
复制 `env_example.txt` 为 `.env` 并配置：
```bash
ALI_API_KEY=your_api_key_here
ALI_MODEL_NAME=qwen3
ALI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

### 数据库配置
系统支持两种数据库模式：
- **单数据库模式**: 使用 `database.py`
- **双数据库模式**: 使用 `result_database.py`

## 📊 数据格式

### CSV导入格式
```csv
origin_id,publish_time,title,content
1,2024-01-01,标题1,内容1
2,2024-01-02,标题2,内容2
```

### 分析结果格式
```json
{
  "companies": [...],
  "tags": [...],
  "sentiment": {...}
}
```

## 🚨 故障排除

### 常见问题

#### 1. 启动失败
```bash
# 检查Python版本
python --version

# 检查依赖
pip list | grep fastapi

# 重新安装依赖
pip install -r requirements.txt
```

#### 2. API连接失败
```bash
# 测试API连接
python test_api.py

# 检查网络连接
ping dashscope.aliyuncs.com
```

#### 3. 端口占用
```bash
# 检查端口占用
netstat -ano | findstr :8000

# 修改端口 (在config.py中)
PORT = 8001
```

## 📞 技术支持

如果遇到问题：
1. 查看控制台错误信息
2. 检查配置文件是否正确
3. 运行测试脚本验证功能
4. 查看相关日志文件

## 🎉 开始使用

现在您可以：
1. 运行 `start.bat` 或 `python main.py`
2. 在浏览器中访问 http://localhost:8000
3. 开始使用舆情分析功能！

---

**注意**: 本系统已修复所有启动脚本问题，现在可以正常使用！
