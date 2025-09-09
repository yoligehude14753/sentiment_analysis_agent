#!/bin/bash

# AWS EC2应用配置脚本 - 第二部分
# 使用方法: sudo bash configure_app.sh

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

APP_DIR="/var/www/sentiment-analysis"
APP_USER="sentiment"

# 检查项目代码是否存在
if [ ! -f "$APP_DIR/main.py" ]; then
    print_error "项目代码未找到，请先上传代码到 $APP_DIR"
    exit 1
fi

print_info "配置Python虚拟环境..."

# 切换到应用目录
cd $APP_DIR

# 设置目录权限
chown -R $APP_USER:$APP_USER $APP_DIR

# 创建Python虚拟环境
sudo -u $APP_USER python3 -m venv venv
print_success "虚拟环境创建完成"

# 激活虚拟环境并安装依赖
print_info "安装Python依赖..."
sudo -u $APP_USER bash -c "
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install gunicorn  # 生产环境WSGI服务器
"
print_success "Python依赖安装完成"

# 配置环境变量
print_info "配置环境变量..."
if [ ! -f "$APP_DIR/.env" ]; then
    sudo -u $APP_USER cp env_example.txt .env
    print_warning "请编辑 $APP_DIR/.env 文件，配置你的阿里云API密钥"
else
    print_info ".env文件已存在"
fi

# 创建日志目录
mkdir -p /var/log/sentiment-analysis
chown $APP_USER:$APP_USER /var/log/sentiment-analysis
print_success "日志目录创建完成"

# 配置Gunicorn
print_info "配置Gunicorn..."
cat > /etc/systemd/system/sentiment-analysis.service << 'EOF'
[Unit]
Description=Sentiment Analysis Gunicorn Application
After=network.target

[Service]
Type=notify
User=sentiment
Group=sentiment
RuntimeDirectory=sentiment-analysis
WorkingDirectory=/var/www/sentiment-analysis
Environment="PATH=/var/www/sentiment-analysis/venv/bin"
ExecStart=/var/www/sentiment-analysis/venv/bin/gunicorn main:app -c gunicorn.conf.py
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

# 创建Gunicorn配置文件
cat > $APP_DIR/gunicorn.conf.py << 'EOF'
# Gunicorn配置文件
import multiprocessing

# 绑定地址和端口
bind = "127.0.0.1:8000"

# 工作进程数
workers = min(multiprocessing.cpu_count() * 2 + 1, 4)

# 工作模式
worker_class = "uvicorn.workers.UvicornWorker"

# 最大请求数
max_requests = 1000
max_requests_jitter = 100

# 超时设置
timeout = 120
keepalive = 5

# 日志设置
accesslog = "/var/log/sentiment-analysis/access.log"
errorlog = "/var/log/sentiment-analysis/error.log"
loglevel = "info"

# 进程名称
proc_name = "sentiment-analysis"

# 预加载应用
preload_app = True

# 用户和组
user = "sentiment"
group = "sentiment"
EOF

chown $APP_USER:$APP_USER $APP_DIR/gunicorn.conf.py

# 配置Nginx
print_info "配置Nginx..."
cat > /etc/nginx/sites-available/sentiment-analysis << 'EOF'
server {
    listen 80;
    server_name _;  # 替换为你的域名

    # 安全头部
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # 客户端最大上传大小
    client_max_body_size 50M;

    # 静态文件
    location /static/ {
        alias /var/www/sentiment-analysis/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # 代理到Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 120s;
        
        # 缓冲设置
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }

    # 健康检查
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

# 启用站点
ln -sf /etc/nginx/sites-available/sentiment-analysis /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# 测试Nginx配置
nginx -t
if [ $? -eq 0 ]; then
    print_success "Nginx配置测试通过"
else
    print_error "Nginx配置有误"
    exit 1
fi

# 启动服务
print_info "启动服务..."
systemctl daemon-reload
systemctl enable sentiment-analysis
systemctl start sentiment-analysis
systemctl enable nginx
systemctl restart nginx

# 检查服务状态
print_info "检查服务状态..."
if systemctl is-active --quiet sentiment-analysis; then
    print_success "Sentiment Analysis服务运行正常"
else
    print_error "Sentiment Analysis服务启动失败"
    systemctl status sentiment-analysis
fi

if systemctl is-active --quiet nginx; then
    print_success "Nginx服务运行正常"
else
    print_error "Nginx服务启动失败"
    systemctl status nginx
fi

# 创建快速脚本
print_info "创建管理脚本..."
cat > /usr/local/bin/sentiment-manage << 'EOF'
#!/bin/bash

case "$1" in
    start)
        systemctl start sentiment-analysis nginx
        echo "服务已启动"
        ;;
    stop)
        systemctl stop sentiment-analysis nginx
        echo "服务已停止"
        ;;
    restart)
        systemctl restart sentiment-analysis nginx
        echo "服务已重启"
        ;;
    status)
        echo "=== Sentiment Analysis 状态 ==="
        systemctl status sentiment-analysis
        echo ""
        echo "=== Nginx 状态 ==="
        systemctl status nginx
        ;;
    logs)
        echo "=== 应用日志 ==="
        tail -f /var/log/sentiment-analysis/error.log
        ;;
    update)
        echo "更新应用..."
        cd /var/www/sentiment-analysis
        git pull
        systemctl restart sentiment-analysis
        echo "应用已更新并重启"
        ;;
    *)
        echo "使用方法: $0 {start|stop|restart|status|logs|update}"
        exit 1
        ;;
esac
EOF

chmod +x /usr/local/bin/sentiment-manage

print_success "🎉 应用配置完成！"
print_info "服务管理命令:"
echo "  启动服务: sentiment-manage start"
echo "  停止服务: sentiment-manage stop"  
echo "  重启服务: sentiment-manage restart"
echo "  查看状态: sentiment-manage status"
echo "  查看日志: sentiment-manage logs"
echo "  更新应用: sentiment-manage update"
echo ""
print_info "请确保编辑 $APP_DIR/.env 文件配置API密钥"
print_info "访问地址: http://your-ec2-ip/"






