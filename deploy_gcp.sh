#!/bin/bash

# GCP虚拟机部署脚本 - 一键部署情感分析系统到GCP
# 使用方法: ./deploy_gcp.sh your-gcp-ip your-key-file

set -e

# 检查参数
if [ $# -ne 2 ]; then
    echo "使用方法: $0 <GCP_IP> <KEY_FILE>"
    echo "示例: $0 35.209.254.98 google_compute_engine"
    exit 1
fi

GCP_IP=$1
KEY_FILE=$2

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

# 检查必要文件
if [ ! -f "$KEY_FILE" ]; then
    print_error "密钥文件 $KEY_FILE 不存在"
    exit 1
fi

if [ ! -f "main.py" ]; then
    print_error "请在项目根目录运行此脚本"
    exit 1
fi

print_info "开始一键部署到GCP虚拟机: $GCP_IP"

# 1. 上传部署脚本
print_info "上传部署脚本..."
scp -i "$KEY_FILE" -o StrictHostKeyChecking=no \
    configure_gcp.sh health_check.py \
    anyut@$GCP_IP:/tmp/

print_success "部署脚本上传完成"

# 2. 运行基础环境配置
print_info "配置基础环境..."
ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no anyut@$GCP_IP << 'EOF'
    sudo mv /tmp/configure_gcp.sh /opt/
    sudo mv /tmp/health_check.py /usr/local/bin/
    sudo chmod +x /opt/configure_gcp.sh
    sudo chmod +x /usr/local/bin/health_check.py
    sudo bash /opt/configure_gcp.sh
EOF

print_success "基础环境配置完成"

# 3. 打包并上传项目代码
print_info "打包项目代码..."
tar -czf sentiment-analysis.tar.gz \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='venv' \
    --exclude='node_modules' \
    --exclude='*.db' \
    --exclude='*.log' \
    --exclude='.env' \
    --exclude='deploy_*.sh' \
    --exclude='*.tar.gz' \
    --exclude='test_*' \
    --exclude='*_test.py' \
    .

print_info "上传项目代码..."
scp -i "$KEY_FILE" sentiment-analysis.tar.gz anyut@$GCP_IP:/tmp/

# 清理本地打包文件
rm sentiment-analysis.tar.gz

print_success "项目代码上传完成"

# 4. 部署应用
print_info "部署应用..."
ssh -i "$KEY_FILE" anyut@$GCP_IP << 'EOF'
    cd /tmp
    tar -xzf sentiment-analysis.tar.gz
    sudo mkdir -p /var/www/sentiment-analysis
    sudo cp -r * /var/www/sentiment-analysis/
    sudo chown -R anyut:anyut /var/www/sentiment-analysis
    sudo bash /opt/configure_gcp.sh
EOF

print_success "应用部署完成"

# 5. 配置提醒
print_warning "部署完成！请完成以下配置:"
echo ""
echo "1. 配置API密钥:"
echo "   ssh -i $KEY_FILE anyut@$GCP_IP"
echo "   sudo nano /var/www/sentiment-analysis/.env"
echo ""
echo "2. 重启服务:"
echo "   sudo systemctl restart sentiment-analysis"
echo ""
echo "3. 检查服务状态:"
echo "   sudo systemctl status sentiment-analysis"
echo ""
echo "4. 访问应用:"
echo "   http://$GCP_IP:8000"
echo ""
echo "5. 运行健康检查:"
echo "   python3 /usr/local/bin/health_check.py"

print_info "GCP防火墙设置提醒："
echo "请确保在GCP控制台的防火墙规则中开放以下端口："
echo "- HTTP (8000): 0.0.0.0/0"
echo "- SSH (22): 你的IP地址"

print_success "🎉 GCP一键部署完成！"


