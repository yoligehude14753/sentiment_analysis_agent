# GCP虚拟机部署操作指南

## 🎯 部署目标
将情感分析系统部署到GCP虚拟机 `35.209.254.98`，并通过公网IP访问。

## 📋 部署前准备

### 1. 确认文件准备
请确认以下文件已准备就绪：
- ✅ `deploy_gcp.sh` - 主部署脚本
- ✅ `configure_gcp.sh` - 环境配置脚本  
- ✅ `health_check.py` - 健康检查脚本
- ✅ `main.py` - 应用主文件
- ✅ `requirements.txt` - Python依赖

### 2. 确认SSH连接
```bash
# 测试SSH连接
ssh -i "C:\Users\anyut\.ssh\google_compute_engine" anyut@35.209.254.98
```

## 🚀 部署步骤

### 第一步：执行部署脚本
在项目根目录的PowerShell中执行：

```powershell
# 执行部署（Windows PowerShell）
bash deploy_gcp.sh 35.209.254.98 "C:\Users\anyut\.ssh\google_compute_engine"
```

**预期输出：**
```
ℹ️  开始一键部署到GCP虚拟机: 35.209.254.98
ℹ️  上传部署脚本...
✅ 部署脚本上传完成
ℹ️  配置基础环境...
✅ 基础环境配置完成
ℹ️  打包项目代码...
ℹ️  上传项目代码...
✅ 项目代码上传完成
ℹ️  部署应用...
✅ 应用部署完成
🎉 GCP一键部署完成！
```

### 第二步：配置API密钥
连接到虚拟机并配置API密钥：

```bash
# 连接到虚拟机
ssh -i "C:\Users\anyut\.ssh\google_compute_engine" anyut@35.209.254.98

# 编辑环境配置文件
sudo nano /var/www/sentiment-analysis/.env
```

**更新以下配置：**
```env
# 阿里云通义千问API配置
DASHSCOPE_API_KEY=你的实际API密钥
ALI_MODEL_NAME=qwen-turbo
ALI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# 服务器配置
HOST=0.0.0.0
PORT=8000
DEBUG=False
```

### 第三步：重启服务
```bash
# 重启应用服务
sudo systemctl restart sentiment-analysis

# 检查服务状态
sudo systemctl status sentiment-analysis

# 重启Nginx
sudo systemctl restart nginx
```

**预期输出：**
```
● sentiment-analysis.service - Sentiment Analysis API Service
   Loaded: loaded (/etc/systemd/system/sentiment-analysis.service; enabled; vendor preset: enabled)
   Active: active (running) since [时间]
   Main PID: [进程ID] (python)
   Tasks: 1 (limit: 4915)
   Memory: [内存使用]
   CGroup: /system.slice/sentiment-analysis.service
           └─[进程ID] /var/www/sentiment-analysis/venv/bin/python main.py
```

## 🔧 GCP防火墙配置

### 方法一：通过GCP控制台配置

1. **登录GCP控制台**
   - 访问：https://console.cloud.google.com/
   - 选择您的项目

2. **配置防火墙规则**
   - 左侧菜单：**VPC网络** > **防火墙**
   - 点击：**创建防火墙规则**

3. **创建HTTP访问规则**
   ```
   名称: sentiment-analysis-http
   描述: Allow HTTP access to sentiment analysis application
   网络: default
   优先级: 1000
   方向: 入站
   操作: 允许
   目标: 网络中的所有实例
   来源IP范围: 0.0.0.0/0
   协议和端口: TCP - 80,8000
   ```

4. **保存规则**
   - 点击：**创建**

### 方法二：通过gcloud命令行
```bash
# 创建HTTP访问规则
gcloud compute firewall-rules create sentiment-analysis-http \
    --allow tcp:80,tcp:8000 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow HTTP access to sentiment analysis application"
```

## ✅ 验证部署

### 1. 健康检查
```bash
# 在虚拟机中执行
curl http://localhost:8000/api/health

# 从外部访问
curl http://35.209.254.98/api/health
```

**预期输出：**
```json
{
  "status": "healthy",
  "message": "多Agent情感分析系统运行正常"
}
```

### 2. 访问应用
在浏览器中访问：
- **主页**: http://35.209.254.98
- **API文档**: http://35.209.254.98/docs

### 3. 查看服务状态
```bash
# 查看应用服务状态
sudo systemctl status sentiment-analysis

# 查看Nginx状态
sudo systemctl status nginx

# 查看实时日志
sudo journalctl -u sentiment-analysis -f
```

## 🛠️ 服务管理命令

部署完成后，使用以下命令管理服务：

```bash
# 启动服务
sentiment-manage start

# 停止服务
sentiment-manage stop

# 重启服务
sentiment-manage restart

# 查看状态
sentiment-manage status

# 查看实时日志
sentiment-manage logs

# 更新应用
sentiment-manage update
```

## 🔍 故障排除

### 1. 服务无法启动
```bash
# 检查详细错误
sudo journalctl -u sentiment-analysis --no-pager

# 检查端口占用
sudo netstat -tlnp | grep :8000

# 检查Python环境
cd /var/www/sentiment-analysis
source venv/bin/activate
python --version
pip list
```

### 2. 无法访问应用
```bash
# 检查防火墙状态
sudo ufw status

# 检查Nginx配置
sudo nginx -t

# 测试本地访问
curl http://localhost:8000/api/health
```

### 3. API调用失败
```bash
# 检查API密钥
cat /var/www/sentiment-analysis/.env | grep DASHSCOPE_API_KEY

# 测试API连接
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv('/var/www/sentiment-analysis/.env')
print('API Key configured:', bool(os.getenv('DASHSCOPE_API_KEY')))
"
```

## 📊 性能监控

### 1. 系统资源监控
```bash
# 查看系统资源
htop

# 查看内存使用
free -h

# 查看磁盘使用
df -h
```

### 2. 应用性能监控
```bash
# 查看应用进程
ps aux | grep python

# 查看网络连接
netstat -tlnp | grep :8000

# 查看日志大小
du -sh /var/log/sentiment-analysis/
```

## 🔒 安全建议

### 1. 限制SSH访问
```bash
# 获取您的公网IP
curl ifconfig.me

# 更新SSH防火墙规则（在GCP控制台中）
# 将来源IP范围改为您的IP地址
```

### 2. 定期更新
```bash
# 更新系统包
sudo apt update && sudo apt upgrade -y

# 重启服务
sudo systemctl restart sentiment-analysis
```

### 3. 备份配置
```bash
# 创建备份
sudo cp /var/www/sentiment-analysis/.env /backup/
sudo cp /etc/systemd/system/sentiment-analysis.service /backup/
```

## 📞 技术支持

如果遇到问题，请提供以下信息：

1. **错误日志**：
   ```bash
   sudo journalctl -u sentiment-analysis --no-pager
   ```

2. **服务状态**：
   ```bash
   sudo systemctl status sentiment-analysis
   ```

3. **网络连接测试**：
   ```bash
   curl -I http://35.209.254.98/api/health
   ```

4. **配置文件内容**：
   ```bash
   cat /var/www/sentiment-analysis/.env
   ```

## 🎉 部署完成

部署成功后，您可以通过以下方式访问系统：

- **Web界面**: http://35.209.254.98
- **API接口**: http://35.209.254.98/api/
- **API文档**: http://35.209.254.98/docs
- **健康检查**: http://35.209.254.98/api/health

系统已配置自动重启、日志轮转和健康检查功能，确保稳定运行。

