# 情感分析系统 - GCP虚拟机迁移方案

## 📋 项目概述

本项目已成功适配Linux环境，可直接部署到GCP虚拟机。系统包含完整的部署脚本、配置文件和文档，支持一键部署。

### 🎯 迁移目标
- ✅ 适配Linux环境（Ubuntu/Debian）
- ✅ 创建包含依赖的部署包
- ✅ 配置Nginx反向代理
- ✅ 设置systemd服务自启动
- ✅ 支持通过公网IP访问
- ✅ 提供完整的管理工具

## 🚀 快速开始

### Windows用户
```bash
# 双击运行快速部署工具
quick_deploy.bat

# 或直接运行一键部署
deploy_to_gcp.bat
```

### Linux/Mac用户
```bash
# 一键部署
chmod +x deploy_to_gcp.sh
./deploy_to_gcp.sh

# 或分步部署
chmod +x pack_for_gcp_linux.sh
./pack_for_gcp_linux.sh
```

## 📦 文件结构

### 新增的Linux适配文件
```
├── start_linux.sh                    # Linux启动脚本
├── configure_gcp_linux.sh            # GCP部署配置脚本
├── config_linux.py                   # Linux环境配置文件
├── main_linux.py                     # Linux环境主应用文件
├── pack_for_gcp_linux.sh            # Linux打包脚本
├── deploy_to_gcp.sh                  # 一键部署脚本
├── nginx-sentiment-analysis.conf     # Nginx配置文件
├── deploy_to_gcp.bat                 # Windows批处理部署脚本
├── quick_deploy.bat                  # Windows快速部署工具
└── GCP_LINUX_DEPLOYMENT_GUIDE.md     # 完整部署指南
```

### 核心配置文件
- `config_linux.py`: Linux环境配置，包含生产环境设置
- `main_linux.py`: Linux环境主应用，包含日志和错误处理
- `requirements_production.txt`: 生产环境依赖包

## 🔧 部署流程

### 1. 自动部署（推荐）
```bash
# Windows用户
deploy_to_gcp.bat

# Linux/Mac用户
./deploy_to_gcp.sh
```

### 2. 手动部署
```bash
# 1. 打包项目
./pack_for_gcp_linux.sh

# 2. 上传到虚拟机
scp -i "C:\Users\anyut\.ssh\google_compute_engine" sentiment-analysis-gcp_*.tar.gz anyut@35.209.254.98:/tmp/

# 3. 在虚拟机上部署
ssh -i "C:\Users\anyut\.ssh\google_compute_engine" anyut@35.209.254.98
cd /tmp && tar -xzf sentiment-analysis-gcp_*.tar.gz
cd sentiment-analysis-gcp && sudo bash configure_gcp.sh
```

## 🌐 访问地址

部署完成后，通过以下地址访问：
- **主要访问**: http://35.209.254.98
- **健康检查**: http://35.209.254.98/api/health
- **配置页面**: http://35.209.254.98/config

## 🛠️ 管理命令

### 服务管理
```bash
# 启动服务
sentiment-manage start

# 停止服务
sentiment-manage stop

# 重启服务
sentiment-manage restart

# 查看状态
sentiment-manage status

# 查看日志
sentiment-manage logs
```

### 系统管理
```bash
# 检查服务状态
sudo systemctl status sentiment-analysis
sudo systemctl status nginx

# 查看日志
sudo journalctl -u sentiment-analysis -f
sudo tail -f /var/log/nginx/sentiment-analysis.error.log
```

## ⚙️ 配置说明

### 环境变量配置
```bash
# 编辑配置文件
sudo nano /var/www/sentiment-analysis/.env

# 主要配置项
DASHSCOPE_API_KEY=your_api_key_here    # 阿里云API密钥
HOST=127.0.0.1                         # 服务监听地址
PORT=8000                              # 服务端口
DEBUG=False                            # 调试模式
LOG_LEVEL=INFO                         # 日志级别
```

### API密钥配置
1. 访问 [阿里云控制台](https://dashscope.console.aliyun.com/)
2. 创建API密钥
3. 在`.env`文件中设置`DASHSCOPE_API_KEY`
4. 重启服务：`sudo systemctl restart sentiment-analysis`

## 🔒 安全配置

### 防火墙设置
```bash
# 允许必要端口
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### SSH安全
```bash
# 配置SSH密钥认证
sudo nano /etc/ssh/sshd_config
# 设置 PasswordAuthentication no
sudo systemctl restart ssh
```

## 📊 监控和维护

### 系统监控
```bash
# 检查系统资源
top
free -h
df -h

# 检查服务状态
sudo systemctl status sentiment-analysis
sudo systemctl status nginx

# 检查端口监听
sudo netstat -tlnp | grep :8000
sudo netstat -tlnp | grep :80
```

### 日志管理
```bash
# 应用日志
sudo journalctl -u sentiment-analysis -f

# Nginx日志
sudo tail -f /var/log/nginx/sentiment-analysis.access.log
sudo tail -f /var/log/nginx/sentiment-analysis.error.log

# 应用日志文件
sudo tail -f /var/www/sentiment-analysis/logs/app.log
```

## 🐛 故障排除

### 常见问题

#### 1. 无法访问网站
- 检查防火墙规则
- 检查服务状态
- 查看错误日志

#### 2. API密钥问题
- 检查`.env`文件配置
- 验证API密钥有效性
- 重启服务

#### 3. 服务启动失败
- 检查依赖包安装
- 检查Python虚拟环境
- 检查权限配置

#### 4. 性能问题
- 检查系统资源使用
- 重启服务释放内存
- 优化Nginx配置

## 📞 技术支持

### 获取帮助
1. 查看部署指南：`GCP_LINUX_DEPLOYMENT_GUIDE.md`
2. 检查服务日志
3. 运行健康检查：`curl http://35.209.254.98/api/health`
4. 联系技术支持

### 常用命令速查
```bash
# 服务管理
sudo systemctl start/stop/restart/status sentiment-analysis

# 日志查看
sudo journalctl -u sentiment-analysis -f
sudo tail -f /var/log/nginx/sentiment-analysis.error.log

# 配置管理
sudo nano /var/www/sentiment-analysis/.env
sudo systemctl restart sentiment-analysis

# 健康检查
curl http://localhost/api/health
```

## 🎉 部署完成

恭喜！您的情感分析系统已成功迁移到GCP虚拟机。

### 下一步操作
1. 配置API密钥
2. 测试系统功能
3. 设置监控告警
4. 定期备份数据

### 系统特性
- ✅ 完全适配Linux环境
- ✅ 支持一键部署
- ✅ 包含完整的管理工具
- ✅ 提供详细的部署文档
- ✅ 支持通过公网IP访问
- ✅ 包含Nginx反向代理配置
- ✅ 支持systemd服务管理

---

**迁移成功！** 🎉

现在您可以通过 http://35.209.254.98 访问您的情感分析系统了！


