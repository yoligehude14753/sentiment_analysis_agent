# AWS EC2 部署完整指南

## 🚀 部署步骤

### 第一步：连接到EC2实例

```bash
# 使用SSH连接到你的EC2实例
ssh -i your-key.pem ec2-user@your-ec2-ip

# 或者使用Ubuntu实例
ssh -i your-key.pem ubuntu@your-ec2-ip
```

### 第二步：上传部署脚本

在本地执行（上传部署脚本到EC2）：
```bash
# 上传部署脚本
scp -i your-key.pem deploy_aws.sh ec2-user@your-ec2-ip:/tmp/
scp -i your-key.pem configure_app.sh ec2-user@your-ec2-ip:/tmp/
```

### 第三步：运行基础环境配置

在EC2实例上执行：
```bash
# 移动脚本到合适位置
sudo mv /tmp/deploy_aws.sh /opt/
sudo mv /tmp/configure_app.sh /opt/

# 给脚本执行权限
sudo chmod +x /opt/deploy_aws.sh
sudo chmod +x /opt/configure_app.sh

# 运行基础环境配置
sudo bash /opt/deploy_aws.sh
```

### 第四步：上传项目代码

在本地执行：
```bash
# 打包项目代码（排除不必要的文件）
tar -czf sentiment-analysis.tar.gz \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='venv' \
    --exclude='node_modules' \
    --exclude='*.db' \
    sentiment-analysis-agent/

# 上传到EC2
scp -i your-key.pem sentiment-analysis.tar.gz ec2-user@your-ec2-ip:/tmp/
```

在EC2实例上执行：
```bash
# 解压项目代码
cd /tmp
tar -xzf sentiment-analysis.tar.gz

# 移动到应用目录
sudo mv sentiment-analysis-agent/* /var/www/sentiment-analysis/
sudo chown -R sentiment:sentiment /var/www/sentiment-analysis
```

### 第五步：配置应用环境

```bash
# 运行应用配置脚本
sudo bash /opt/configure_app.sh
```

### 第六步：配置环境变量

```bash
# 编辑环境变量文件
sudo nano /var/www/sentiment-analysis/.env

# 配置以下内容：
DASHSCOPE_API_KEY=your_ali_api_key_here
ALI_MODEL_NAME=qwen-turbo
ALI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
HOST=0.0.0.0
PORT=8000
DEBUG=False
```

### 第七步：启动服务

```bash
# 重启服务以加载新配置
sudo systemctl restart sentiment-analysis

# 检查服务状态
sentiment-manage status
```

## 🔧 配置域名和SSL（可选）

### 配置域名

1. 在你的域名DNS设置中，添加A记录指向EC2的公网IP
2. 修改Nginx配置：

```bash
sudo nano /etc/nginx/sites-available/sentiment-analysis

# 修改server_name行：
server_name your-domain.com www.your-domain.com;
```

### 配置SSL证书

```bash
# 使用Let's Encrypt获取免费SSL证书
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# 设置自动续期
sudo crontab -e
# 添加以下行：
0 12 * * * /usr/bin/certbot renew --quiet
```

## 📊 监控和维护

### 服务管理命令

```bash
# 查看应用状态
sentiment-manage status

# 查看实时日志
sentiment-manage logs

# 重启服务
sentiment-manage restart

# 更新应用（如果使用Git）
sentiment-manage update
```

### 系统监控

```bash
# 查看系统资源使用
htop

# 查看磁盘使用
df -h

# 查看内存使用
free -h

# 查看网络连接
netstat -tulpn
```

### 日志文件位置

- 应用日志：`/var/log/sentiment-analysis/`
- Nginx日志：`/var/log/nginx/`
- 系统日志：`/var/log/syslog`

## 🔒 安全设置

### 1. EC2安全组配置

在AWS控制台配置安全组规则：

**入站规则：**
- HTTP (80): 0.0.0.0/0
- HTTPS (443): 0.0.0.0/0  
- SSH (22): 你的IP地址

**出站规则：**
- 所有流量: 0.0.0.0/0

### 2. 系统安全设置

```bash
# 配置SSH安全
sudo nano /etc/ssh/sshd_config

# 建议修改：
PermitRootLogin no
PasswordAuthentication no
Port 2222  # 修改SSH端口（可选）

# 重启SSH服务
sudo systemctl restart ssh

# 更新防火墙规则（如果修改了SSH端口）
sudo ufw allow 2222
sudo ufw delete allow ssh
```

### 3. 自动备份设置

```bash
# 创建备份脚本
sudo nano /usr/local/bin/backup-sentiment.sh

#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups"
APP_DIR="/var/www/sentiment-analysis"

mkdir -p $BACKUP_DIR

# 备份应用数据
tar -czf $BACKUP_DIR/sentiment-backup-$DATE.tar.gz \
    $APP_DIR/*.db \
    $APP_DIR/.env \
    $APP_DIR/config/

# 删除7天前的备份
find $BACKUP_DIR -name "sentiment-backup-*.tar.gz" -mtime +7 -delete

# 给脚本执行权限
sudo chmod +x /usr/local/bin/backup-sentiment.sh

# 设置每日自动备份
sudo crontab -e
# 添加：
0 2 * * * /usr/local/bin/backup-sentiment.sh
```

## 🚨 故障排除

### 常见问题

#### 1. 服务无法启动

```bash
# 查看详细错误信息
sudo journalctl -u sentiment-analysis -f

# 检查Python环境
sudo -u sentiment bash -c "cd /var/www/sentiment-analysis && source venv/bin/activate && python main.py"
```

#### 2. 502 Bad Gateway错误

```bash
# 检查Gunicorn服务状态
sudo systemctl status sentiment-analysis

# 检查端口占用
sudo netstat -tulpn | grep 8000

# 重启服务
sudo systemctl restart sentiment-analysis nginx
```

#### 3. 磁盘空间不足

```bash
# 清理日志文件
sudo journalctl --vacuum-time=7d
sudo find /var/log -name "*.log" -mtime +7 -delete

# 清理临时文件
sudo apt autoremove
sudo apt autoclean
```

## 📈 性能优化

### 1. 调整Gunicorn配置

```bash
# 编辑Gunicorn配置
sudo nano /var/www/sentiment-analysis/gunicorn.conf.py

# 根据服务器配置调整workers数量
workers = 4  # 对于4核服务器
```

### 2. 配置Redis缓存（可选）

```bash
# 安装Redis
sudo apt install redis-server

# 启动Redis
sudo systemctl enable redis-server
sudo systemctl start redis-server

# 在应用中配置Redis缓存
```

### 3. 数据库优化

```bash
# 定期清理数据库
sudo -u sentiment bash -c "
    cd /var/www/sentiment-analysis
    source venv/bin/activate
    python -c 'from database import DatabaseManager; db = DatabaseManager(); db.vacuum_database()'
"
```

## 📞 技术支持

如果遇到问题，请检查：

1. **服务状态**：`sentiment-manage status`
2. **应用日志**：`sentiment-manage logs`
3. **系统资源**：`htop`
4. **网络连接**：`curl http://localhost:8000`

常用调试命令：
```bash
# 测试应用启动
sudo -u sentiment bash -c "cd /var/www/sentiment-analysis && source venv/bin/activate && python main.py"

# 测试Nginx配置
sudo nginx -t

# 重新加载配置
sudo systemctl daemon-reload
```






