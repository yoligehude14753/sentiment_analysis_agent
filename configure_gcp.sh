#!/bin/bash

# GCP虚拟机环境配置脚本
# 配置Python环境、依赖包、系统服务等

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info "开始配置GCP虚拟机环境..."

# 1. 更新系统包
print_info "更新系统包..."
sudo apt update && sudo apt upgrade -y

# 2. 安装Python 3.9+和pip
print_info "安装Python环境..."
sudo apt install -y python3 python3-pip python3-venv python3-dev

# 3. 安装系统依赖
print_info "安装系统依赖..."
sudo apt install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libjpeg-dev \
    libpng-dev \
    curl \
    wget \
    git \
    nginx \
    supervisor

# 4. 创建应用用户（如果不存在）
if ! id "sentiment" &>/dev/null; then
    print_info "创建应用用户..."
    sudo useradd -m -s /bin/bash sentiment
    sudo usermod -aG sudo sentiment
fi

# 5. 创建应用目录
print_info "创建应用目录..."
sudo mkdir -p /var/www/sentiment-analysis
sudo mkdir -p /var/log/sentiment-analysis
sudo mkdir -p /var/run/sentiment-analysis

# 6. 设置目录权限
sudo chown -R sentiment:sentiment /var/www/sentiment-analysis
sudo chown -R sentiment:sentiment /var/log/sentiment-analysis
sudo chown -R sentiment:sentiment /var/run/sentiment-analysis

# 7. 创建Python虚拟环境
print_info "创建Python虚拟环境..."
cd /var/www/sentiment-analysis
sudo -u sentiment python3 -m venv venv

# 8. 激活虚拟环境并安装依赖
print_info "安装Python依赖..."
sudo -u sentiment bash -c "
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
"

# 9. 创建环境配置文件
print_info "创建环境配置文件..."
sudo -u sentiment tee /var/www/sentiment-analysis/.env > /dev/null << 'EOF'
# 阿里云通义千问API配置
DASHSCOPE_API_KEY=your_dashscope_api_key_here
ALI_MODEL_NAME=qwen-turbo
ALI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# 服务器配置
HOST=0.0.0.0
PORT=8000
DEBUG=False

# 数据文件路径
DATA_FILE_PATH=/var/www/sentiment-analysis/data/sentiment_data.csv
EOF

# 10. 创建数据目录
sudo mkdir -p /var/www/sentiment-analysis/data
sudo chown -R sentiment:sentiment /var/www/sentiment-analysis/data

# 11. 创建systemd服务文件
print_info "创建systemd服务..."
sudo tee /etc/systemd/system/sentiment-analysis.service > /dev/null << 'EOF'
[Unit]
Description=Sentiment Analysis API Service
After=network.target

[Service]
Type=simple
User=sentiment
Group=sentiment
WorkingDirectory=/var/www/sentiment-analysis
Environment=PATH=/var/www/sentiment-analysis/venv/bin
ExecStart=/var/www/sentiment-analysis/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=sentiment-analysis

[Install]
WantedBy=multi-user.target
EOF

# 12. 创建Nginx配置
print_info "配置Nginx反向代理..."
sudo tee /etc/nginx/sites-available/sentiment-analysis > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;

    # 增加客户端请求体大小限制
    client_max_body_size 50M;

    # 增加超时设置
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 支持WebSocket和SSE
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 禁用缓冲以支持流式响应
        proxy_buffering off;
        proxy_cache off;
    }

    # 静态文件处理
    location /static/ {
        alias /var/www/sentiment-analysis/static/;
        expires 1h;
        add_header Cache-Control "public, immutable";
    }

    # 健康检查
    location /api/health {
        proxy_pass http://127.0.0.1:8000/api/health;
        access_log off;
    }
}
EOF

# 13. 启用Nginx站点
sudo ln -sf /etc/nginx/sites-available/sentiment-analysis /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# 14. 测试Nginx配置
sudo nginx -t

# 15. 启动和启用服务
print_info "启动服务..."
sudo systemctl daemon-reload
sudo systemctl enable sentiment-analysis
sudo systemctl start sentiment-analysis
sudo systemctl enable nginx
sudo systemctl restart nginx

# 16. 创建日志轮转配置
print_info "配置日志轮转..."
sudo tee /etc/logrotate.d/sentiment-analysis > /dev/null << 'EOF'
/var/log/sentiment-analysis/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 sentiment sentiment
    postrotate
        systemctl reload sentiment-analysis
    endscript
}
EOF

# 17. 创建健康检查脚本
print_info "创建健康检查脚本..."
sudo tee /usr/local/bin/sentiment-health-check > /dev/null << 'EOF'
#!/bin/bash

# 健康检查脚本
API_URL="http://localhost:8000/api/health"
LOG_FILE="/var/log/sentiment-analysis/health-check.log"

# 检查API是否响应
if curl -f -s "$API_URL" > /dev/null; then
    echo "$(date): API健康检查通过" >> "$LOG_FILE"
    exit 0
else
    echo "$(date): API健康检查失败" >> "$LOG_FILE"
    # 尝试重启服务
    systemctl restart sentiment-analysis
    exit 1
fi
EOF

sudo chmod +x /usr/local/bin/sentiment-health-check

# 18. 创建定时健康检查
print_info "配置定时健康检查..."
sudo tee /etc/cron.d/sentiment-health-check > /dev/null << 'EOF'
# 每5分钟检查一次服务健康状态
*/5 * * * * root /usr/local/bin/sentiment-health-check
EOF

# 19. 设置防火墙规则（如果使用ufw）
if command -v ufw &> /dev/null; then
    print_info "配置防火墙..."
    sudo ufw allow 22/tcp
    sudo ufw allow 80/tcp
    sudo ufw allow 8000/tcp
    sudo ufw --force enable
fi

# 20. 创建管理脚本
print_info "创建管理脚本..."
sudo tee /usr/local/bin/sentiment-manage > /dev/null << 'EOF'
#!/bin/bash

case "$1" in
    start)
        sudo systemctl start sentiment-analysis
        echo "服务已启动"
        ;;
    stop)
        sudo systemctl stop sentiment-analysis
        echo "服务已停止"
        ;;
    restart)
        sudo systemctl restart sentiment-analysis
        echo "服务已重启"
        ;;
    status)
        sudo systemctl status sentiment-analysis
        ;;
    logs)
        sudo journalctl -u sentiment-analysis -f
        ;;
    update)
        cd /var/www/sentiment-analysis
        sudo -u sentiment git pull
        sudo -u sentiment bash -c "source venv/bin/activate && pip install -r requirements.txt"
        sudo systemctl restart sentiment-analysis
        echo "应用已更新"
        ;;
    *)
        echo "使用方法: $0 {start|stop|restart|status|logs|update}"
        exit 1
        ;;
esac
EOF

sudo chmod +x /usr/local/bin/sentiment-manage

# 21. 检查服务状态
print_info "检查服务状态..."
sleep 5
if sudo systemctl is-active --quiet sentiment-analysis; then
    print_success "sentiment-analysis服务运行正常"
else
    print_error "sentiment-analysis服务启动失败"
    sudo systemctl status sentiment-analysis
fi

if sudo systemctl is-active --quiet nginx; then
    print_success "Nginx服务运行正常"
else
    print_error "Nginx服务启动失败"
    sudo systemctl status nginx
fi

print_success "GCP环境配置完成！"
print_info "服务管理命令:"
echo "  sentiment-manage start    - 启动服务"
echo "  sentiment-manage stop     - 停止服务"
echo "  sentiment-manage restart  - 重启服务"
echo "  sentiment-manage status   - 查看状态"
echo "  sentiment-manage logs     - 查看日志"
echo "  sentiment-manage update   - 更新应用"

