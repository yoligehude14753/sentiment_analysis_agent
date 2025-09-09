# GCP虚拟机部署指南

## 概述
本指南将帮助您将情感分析系统部署到Google Cloud Platform (GCP) 虚拟机上，并通过公网IP访问。

## 前提条件
- GCP虚拟机已创建并运行
- 虚拟机公网IP: `35.209.254.98`
- SSH密钥文件: `C:\Users\anyut\.ssh\google_compute_engine`
- 本地项目代码完整

## 部署步骤

### 第一步：准备部署文件
在本地项目根目录下，确保以下文件存在：
- `deploy_gcp.sh` - 主部署脚本
- `configure_gcp.sh` - 环境配置脚本
- `health_check.py` - 健康检查脚本
- `main.py` - 应用主文件
- `requirements.txt` - Python依赖

### 第二步：执行部署
在本地项目根目录打开PowerShell，执行：

```bash
# 给脚本执行权限
chmod +x deploy_gcp.sh

# 执行部署
./deploy_gcp.sh 35.209.254.98 "C:\Users\anyut\.ssh\google_compute_engine"
```

### 第三步：配置API密钥
部署完成后，需要配置阿里云API密钥：

```bash
# 连接到虚拟机
ssh -i "C:\Users\anyut\.ssh\google_compute_engine" anyut@35.209.254.98

# 编辑环境配置文件
sudo nano /var/www/sentiment-analysis/.env
```

在`.env`文件中更新以下配置：
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

### 第四步：重启服务
```bash
# 重启应用服务
sudo systemctl restart sentiment-analysis

# 检查服务状态
sudo systemctl status sentiment-analysis

# 重启Nginx
sudo systemctl restart nginx
```

### 第五步：配置GCP防火墙
在GCP控制台中配置防火墙规则：

1. 进入 **VPC网络** > **防火墙**
2. 创建新的防火墙规则：
   - **名称**: `sentiment-analysis-http`
   - **方向**: 入站
   - **操作**: 允许
   - **目标**: 网络中的所有实例
   - **来源IP范围**: `0.0.0.0/0`
   - **协议和端口**: 
     - TCP端口 `80` (HTTP)
     - TCP端口 `8000` (应用端口)
   - **优先级**: 1000

### 第六步：验证部署
1. **健康检查**：
   ```bash
   curl http://35.209.254.98/api/health
   ```

2. **访问应用**：
   在浏览器中访问：`http://35.209.254.98`

3. **查看日志**：
   ```bash
   # 查看应用日志
   sudo journalctl -u sentiment-analysis -f
   
   # 查看Nginx日志
   sudo tail -f /var/log/nginx/access.log
   sudo tail -f /var/log/nginx/error.log
   ```

## 服务管理命令

部署完成后，您可以使用以下命令管理服务：

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

## 故障排除

### 1. 服务无法启动
```bash
# 检查服务状态
sudo systemctl status sentiment-analysis

# 查看详细错误日志
sudo journalctl -u sentiment-analysis --no-pager

# 检查端口占用
sudo netstat -tlnp | grep :8000
```

### 2. 无法访问应用
```bash
# 检查防火墙状态
sudo ufw status

# 检查Nginx状态
sudo systemctl status nginx

# 测试本地访问
curl http://localhost:8000/api/health
```

### 3. API调用失败
```bash
# 检查API密钥配置
cat /var/www/sentiment-analysis/.env

# 测试API连接
python3 -c "
import requests
import os
from dotenv import load_dotenv
load_dotenv('/var/www/sentiment-analysis/.env')
print('API Key:', os.getenv('DASHSCOPE_API_KEY')[:10] + '...')
"
```

### 4. 数据库问题
```bash
# 检查数据库文件权限
ls -la /var/www/sentiment-analysis/data/

# 重新创建数据库
cd /var/www/sentiment-analysis
sudo -u sentiment python3 -c "
from database import init_database
init_database()
print('数据库初始化完成')
"
```

## 性能优化

### 1. 系统资源监控
```bash
# 查看系统资源使用情况
htop

# 查看内存使用
free -h

# 查看磁盘使用
df -h
```

### 2. 应用性能调优
在`/var/www/sentiment-analysis/.env`中添加：
```env
# 性能配置
WORKERS=4
MAX_REQUESTS=1000
TIMEOUT=30
```

### 3. Nginx优化
编辑`/etc/nginx/nginx.conf`：
```nginx
worker_processes auto;
worker_connections 1024;

http {
    gzip on;
    gzip_types text/plain application/json application/javascript text/css;
    
    client_max_body_size 50M;
    client_body_timeout 60s;
    client_header_timeout 60s;
}
```

## 安全建议

1. **定期更新系统**：
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **配置SSL证书**（可选）：
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

3. **限制SSH访问**：
   ```bash
   # 编辑SSH配置
   sudo nano /etc/ssh/sshd_config
   
   # 重启SSH服务
   sudo systemctl restart ssh
   ```

4. **定期备份**：
   ```bash
   # 创建备份脚本
   sudo tee /usr/local/bin/backup-sentiment > /dev/null << 'EOF'
   #!/bin/bash
   BACKUP_DIR="/backup/sentiment-$(date +%Y%m%d)"
   mkdir -p "$BACKUP_DIR"
   cp -r /var/www/sentiment-analysis "$BACKUP_DIR/"
   tar -czf "$BACKUP_DIR.tar.gz" "$BACKUP_DIR"
   rm -rf "$BACKUP_DIR"
   EOF
   
   sudo chmod +x /usr/local/bin/backup-sentiment
   ```

## 监控和维护

### 1. 设置监控告警
在GCP控制台中设置监控告警：
- CPU使用率 > 80%
- 内存使用率 > 85%
- 磁盘使用率 > 90%

### 2. 日志管理
```bash
# 配置日志轮转
sudo nano /etc/logrotate.d/sentiment-analysis

# 清理旧日志
sudo find /var/log -name "*.log" -mtime +30 -delete
```

### 3. 定期维护
```bash
# 每周执行一次
sudo apt update && sudo apt upgrade -y
sudo systemctl restart sentiment-analysis
sudo systemctl restart nginx
```

## 联系支持

如果遇到问题，请提供以下信息：
1. 错误日志：`sudo journalctl -u sentiment-analysis --no-pager`
2. 系统状态：`sudo systemctl status sentiment-analysis`
3. 网络连接：`curl -I http://35.209.254.98/api/health`
4. 配置文件：`cat /var/www/sentiment-analysis/.env`

