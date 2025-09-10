#!/bin/bash

# GCP Linux 部署打包脚本 v3.0
# 专为Linux环境优化，包含离线依赖包

set -e

echo "=========================================="
echo "   开始打包舆情分析系统 for GCP Linux"
echo "=========================================="

# 配置变量
PROJECT_NAME="sentiment-analysis-agent"
VERSION=$(date +"%Y%m%d_%H%M%S")
PACKAGE_NAME="${PROJECT_NAME}-gcp-linux-${VERSION}"
TEMP_DIR="/tmp/${PACKAGE_NAME}"
FINAL_PACKAGE="${PACKAGE_NAME}.tar.gz"

# 清理之前的打包文件
echo "   清理之前的打包文件..."
rm -f sentiment-analysis-*.tar.gz
rm -f sentiment-analysis-*.zip
rm -rf /tmp/sentiment-analysis-*

# 创建临时目录
echo "   创建临时目录: ${TEMP_DIR}"
mkdir -p "${TEMP_DIR}"

# 复制项目文件（排除不需要的文件）
echo "   复制项目文件..."
rsync -av --exclude='.git' \
          --exclude='__pycache__' \
          --exclude='*.pyc' \
          --exclude='.pytest_cache' \
          --exclude='*.log' \
          --exclude='*.db' \
          --exclude='exports/' \
          --exclude='data/' \
          --exclude='missing_files/' \
          --exclude='.artifacts/' \
          --exclude='*.tar.gz' \
          --exclude='*.zip' \
          --exclude='deploy_*.sh' \
          --exclude='deploy_*.bat' \
          --exclude='pack_*.sh' \
          --exclude='pack_*.bat' \
          --exclude='configure_*.sh' \
          --exclude='setup_*.sh' \
          --exclude='setup_*.bat' \
          --exclude='test_*.py' \
          --exclude='check_*.py' \
          --exclude='*_report.py' \
          --exclude='*_fixes*.py' \
          --exclude='*.md' \
          --exclude='*.txt' \
          --exclude='LICENSE' \
          --exclude='.gitignore' \
          --exclude='env_example.txt' \
          --exclude='*.conf' \
          --exclude='*.bat' \
          --exclude='*.sh' \
          . "${TEMP_DIR}/"

# 创建Linux专用的启动脚本
echo "🔧 创建Linux启动脚本..."
cat > "${TEMP_DIR}/start_linux.sh" << 'START_EOF'
#!/bin/bash

# 舆情分析系统 Linux 启动脚本

set -e

echo "=========================================="
echo "🚀 启动舆情分析系统"
echo "=========================================="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装Python3"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建Python虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "📥 安装Python依赖..."
if [ -f "requirements.txt" ]; then
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo "❌ requirements.txt 文件不存在"
    exit 1
fi

# 创建必要的目录
echo "   创建必要目录..."
mkdir -p data
mkdir -p exports
mkdir -p logs

# 设置权限
chmod +x main.py

# 启动应用
echo "   启动Web服务..."
echo "📍 访问地址: http://localhost:8000"
echo "📊 管理界面: http://localhost:8000/config"
echo "💬 智能聊天: 点击右下角聊天图标"
echo ""
echo "按 Ctrl+C 停止服务"
echo "=========================================="

# 使用uvicorn启动
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
START_EOF

chmod +x "${TEMP_DIR}/start_linux.sh"

# 创建systemd服务文件
echo "   创建systemd服务文件..."
cat > "${TEMP_DIR}/sentiment-analysis.service" << 'SERVICE_EOF'
[Unit]
Description=Sentiment Analysis Agent Service
After=network.target

[Service]
Type=simple
User=anyut
Group=anyut
WorkingDirectory=/home/anyut/sentiment-analysis-agent
Environment=PATH=/home/anyut/sentiment-analysis-agent/venv/bin
ExecStart=/home/anyut/sentiment-analysis-agent/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE_EOF

# 创建Nginx配置
echo "🔧 创建Nginx配置..."
cat > "${TEMP_DIR}/nginx-sentiment-analysis.conf" << 'NGINX_EOF'
server {
    listen 80;
    server_name _;  # 替换为您的域名

    # 静态文件
    location /static/ {
        alias /home/anyut/sentiment-analysis-agent/static/;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }

    # API和主应用
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 健康检查
    location /api/health {
        proxy_pass http://127.0.0.1:8000/api/health;
        access_log off;
    }
}
NGINX_EOF

# 创建部署脚本
echo "🔧 创建部署脚本..."
cat > "${TEMP_DIR}/deploy_to_gcp.sh" << 'DEPLOY_EOF'
#!/bin/bash

# GCP Linux 部署脚本

set -e

echo "=========================================="
echo "🚀 开始部署舆情分析系统到GCP"
echo "=========================================="

# 检查是否为root用户
if [ "$EUID" -eq 0 ]; then
    echo "❌ 请不要使用root用户运行此脚本"
    exit 1
fi

# 设置变量
APP_DIR="/home/anyut/sentiment-analysis-agent"
SERVICE_NAME="sentiment-analysis"
NGINX_CONFIG="/etc/nginx/sites-available/sentiment-analysis"

# 停止现有服务
echo "🛑 停止现有服务..."
sudo systemctl stop ${SERVICE_NAME} 2>/dev/null || true
sudo systemctl disable ${SERVICE_NAME} 2>/dev/null || true

# 备份现有应用
if [ -d "${APP_DIR}" ]; then
    echo "💾 备份现有应用..."
    sudo mv "${APP_DIR}" "${APP_DIR}.backup.$(date +%Y%m%d_%H%M%S)" 2>/dev/null || true
fi

# 创建应用目录
echo "   创建应用目录..."
sudo mkdir -p "${APP_DIR}"
sudo chown anyut:anyut "${APP_DIR}"

# 复制应用文件
echo "   复制应用文件..."
cp -r . "${APP_DIR}/"
cd "${APP_DIR}"

# 设置权限
echo "   设置文件权限..."
chmod +x start_linux.sh
chmod +x main.py

# 创建Python虚拟环境
echo "🐍 创建Python虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 升级pip
echo "⬆️ 升级pip..."
pip install --upgrade pip

# 安装依赖
echo "   安装Python依赖..."
pip install -r requirements.txt

# 安装Nginx（如果未安装）
echo "🌐 安装Nginx..."
sudo apt update
sudo apt install -y nginx

# 配置Nginx
echo "🔧 配置Nginx..."
sudo cp nginx-sentiment-analysis.conf ${NGINX_CONFIG}
sudo ln -sf ${NGINX_CONFIG} /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# 测试Nginx配置
echo "   测试Nginx配置..."
sudo nginx -t

# 配置systemd服务
echo "🔧 配置systemd服务..."
sudo cp sentiment-analysis.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}

# 启动服务
echo "🚀 启动服务..."
sudo systemctl start ${SERVICE_NAME}
sudo systemctl restart nginx

# 检查服务状态
echo "   检查服务状态..."
sleep 5
sudo systemctl status ${SERVICE_NAME} --no-pager
sudo systemctl status nginx --no-pager

# 显示访问信息
echo "=========================================="
echo "✅ 部署完成！"
echo "=========================================="
echo "🌐 应用地址: http://$(curl -s ifconfig.me)"
echo "📊 管理界面: http://$(curl -s ifconfig.me)/config"
echo "💬 智能聊天: 点击右下角聊天图标"
echo ""
echo "📋 服务管理命令:"
echo "  启动服务: sudo systemctl start ${SERVICE_NAME}"
echo "  停止服务: sudo systemctl stop ${SERVICE_NAME}"
echo "  重启服务: sudo systemctl restart ${SERVICE_NAME}"
echo "  查看日志: sudo journalctl -u ${SERVICE_NAME} -f"
echo "  查看状态: sudo systemctl status ${SERVICE_NAME}"
echo ""
echo "   Nginx管理命令:"
echo "  重启Nginx: sudo systemctl restart nginx"
echo "  查看Nginx状态: sudo systemctl status nginx"
echo "  查看Nginx日志: sudo tail -f /var/log/nginx/error.log"
echo "=========================================="
DEPLOY_EOF

chmod +x "${TEMP_DIR}/deploy_to_gcp.sh"

# 创建健康检查脚本
echo "   创建健康检查脚本..."
cat > "${TEMP_DIR}/health_check.sh" << 'HEALTH_EOF'
#!/bin/bash

# 健康检查脚本

echo "=========================================="
echo "   舆情分析系统健康检查"
echo "=========================================="

# 检查服务状态
echo "📊 检查服务状态..."
sudo systemctl is-active sentiment-analysis
sudo systemctl is-active nginx

# 检查端口
echo "   检查端口..."
netstat -tlnp | grep :8000 || echo "❌ 端口8000未监听"
netstat -tlnp | grep :80 || echo "❌ 端口80未监听"

# 检查应用响应
echo "   检查应用响应..."
curl -s http://localhost:8000/api/health || echo "❌ 应用无响应"

# 检查Nginx响应
echo "   检查Nginx响应..."
curl -s http://localhost/ | head -5 || echo "❌ Nginx无响应"

echo "=========================================="
echo "✅ 健康检查完成"
echo "=========================================="
HEALTH_EOF

chmod +x "${TEMP_DIR}/health_check.sh"

# 创建requirements.txt（确保包含所有依赖）
echo "📋 创建完整的requirements.txt..."
cat > "${TEMP_DIR}/requirements.txt" << 'REQ_EOF'
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
python-multipart==0.0.6
requests==2.31.0
Jinja2==3.1.2
pandas>=1.3.0
openpyxl>=3.0.0
redis>=4.5.0
playwright==1.54.0
pytest==8.4.1
pytest-playwright==0.7.0
pytest-asyncio==0.21.1
cryptography>=3.4.8
python-dotenv>=0.19.0
aiofiles>=0.8.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
sqlalchemy>=1.4.0
alembic>=1.8.0
psycopg2-binary>=2.9.0
REQ_EOF

# 创建环境配置文件
echo "   创建环境配置文件..."
cat > "${TEMP_DIR}/.env.example" << 'ENV_EOF'
# 阿里云API配置
ALI_API_KEY=your_api_key_here
ALI_MODEL_NAME=qwen-plus
ALI_BASE_URL=https://dashscope.aliyuncs.com/api/v1

# 应用配置
HOST=0.0.0.0
PORT=8000
DEBUG=False
MAX_CONTENT_LENGTH=10485760
BATCH_SIZE=10

# 数据库配置
DATABASE_URL=sqlite:///./data/analysis_results.db

# 安全配置
SECRET_KEY=your_secret_key_here
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENV_EOF

# 打包
echo "📦 打包项目..."
cd /tmp
tar -czf "${FINAL_PACKAGE}" "${PACKAGE_NAME}"

# 移动到当前目录
mv "${FINAL_PACKAGE}" "$(pwd)/"

# 清理临时目录
rm -rf "${TEMP_DIR}"

# 显示结果
echo "=========================================="
echo "✅ 打包完成！"
echo "=========================================="
echo "📦 部署包: ${FINAL_PACKAGE}"
echo "📏 文件大小: $(du -h ${FINAL_PACKAGE} | cut -f1)"
echo ""
echo "   部署步骤:"
echo "1. 上传 ${FINAL_PACKAGE} 到GCP虚拟机"
echo "2. 解压: tar -xzf ${FINAL_PACKAGE}"
echo "3. 进入目录: cd ${PACKAGE_NAME}"
echo "4. 运行部署: ./deploy_to_gcp.sh"
echo ""
echo "   部署后访问: http://YOUR_VM_IP"
echo "=========================================="