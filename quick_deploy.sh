#!/bin/bash

# 快速部署脚本 - 一键部署到AWS EC2
# 使用方法: ./quick_deploy.sh your-ec2-ip your-key.pem

set -e

# 检查参数
if [ $# -ne 2 ]; then
    echo "使用方法: $0 <EC2_IP> <KEY_FILE>"
    echo "示例: $0 3.123.45.67 my-key.pem"
    exit 1
fi

EC2_IP=$1
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

print_info "开始一键部署到AWS EC2: $EC2_IP"

# 1. 上传部署脚本
print_info "上传部署脚本..."
scp -i "$KEY_FILE" -o StrictHostKeyChecking=no \
    deploy_aws.sh configure_app.sh health_check.py \
    ec2-user@$EC2_IP:/tmp/

print_success "部署脚本上传完成"

# 2. 运行基础环境配置
print_info "配置基础环境..."
ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no ec2-user@$EC2_IP << 'EOF'
    sudo mv /tmp/deploy_aws.sh /opt/
    sudo mv /tmp/configure_app.sh /opt/
    sudo mv /tmp/health_check.py /usr/local/bin/
    sudo chmod +x /opt/deploy_aws.sh
    sudo chmod +x /opt/configure_app.sh
    sudo chmod +x /usr/local/bin/health_check.py
    sudo bash /opt/deploy_aws.sh
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
    .

print_info "上传项目代码..."
scp -i "$KEY_FILE" sentiment-analysis.tar.gz ec2-user@$EC2_IP:/tmp/

# 清理本地打包文件
rm sentiment-analysis.tar.gz

print_success "项目代码上传完成"

# 4. 部署应用
print_info "部署应用..."
ssh -i "$KEY_FILE" ec2-user@$EC2_IP << 'EOF'
    cd /tmp
    tar -xzf sentiment-analysis.tar.gz
    sudo mkdir -p /var/www/sentiment-analysis
    sudo cp -r * /var/www/sentiment-analysis/
    sudo chown -R sentiment:sentiment /var/www/sentiment-analysis
    sudo bash /opt/configure_app.sh
EOF

print_success "应用部署完成"

# 5. 配置提醒
print_warning "部署完成！请完成以下配置:"
echo ""
echo "1. 配置API密钥:"
echo "   ssh -i $KEY_FILE ec2-user@$EC2_IP"
echo "   sudo nano /var/www/sentiment-analysis/.env"
echo ""
echo "2. 重启服务:"
echo "   sudo systemctl restart sentiment-analysis"
echo ""
echo "3. 检查服务状态:"
echo "   sentiment-manage status"
echo ""
echo "4. 访问应用:"
echo "   http://$EC2_IP"
echo ""
echo "5. 运行健康检查:"
echo "   python3 /usr/local/bin/health_check.py"

print_info "AWS安全组设置提醒："
echo "请确保在AWS控制台的安全组中开放以下端口："
echo "- HTTP (80): 0.0.0.0/0"
echo "- HTTPS (443): 0.0.0.0/0"
echo "- SSH (22): 你的IP地址"

print_success "🎉 一键部署完成！"

