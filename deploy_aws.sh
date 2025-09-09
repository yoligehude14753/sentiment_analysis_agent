#!/bin/bash

# AWS EC2部署脚本 - 情感分析系统
# 使用方法: sudo bash deploy_aws.sh

set -e  # 出错时退出

echo "🚀 开始部署情感分析系统到AWS EC2..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印彩色信息
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

# 检查是否为root用户
if [[ $EUID -ne 0 ]]; then
   print_error "请使用sudo运行此脚本"
   exit 1
fi

# 1. 更新系统
print_info "更新系统包..."
apt update && apt upgrade -y
print_success "系统更新完成"

# 2. 安装基础依赖
print_info "安装基础依赖..."
apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    nginx \
    supervisor \
    git \
    curl \
    wget \
    unzip \
    htop \
    vim \
    ufw \
    certbot \
    python3-certbot-nginx

print_success "基础依赖安装完成"

# 3. 配置防火墙
print_info "配置防火墙..."
ufw --force enable
ufw allow ssh
ufw allow 80
ufw allow 443
ufw allow 8000  # 临时允许，后续会通过nginx代理
print_success "防火墙配置完成"

# 4. 创建应用用户和目录
print_info "创建应用用户和目录..."
if ! id "sentiment" &>/dev/null; then
    useradd -m -s /bin/bash sentiment
    print_success "用户 sentiment 创建成功"
else
    print_warning "用户 sentiment 已存在"
fi

# 创建应用目录
mkdir -p /var/www/sentiment-analysis
chown sentiment:sentiment /var/www/sentiment-analysis
print_success "应用目录创建完成"

# 5. 安装Node.js (如果需要前端构建)
print_info "安装Node.js..."
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt-get install -y nodejs
print_success "Node.js安装完成"

print_success "🎉 基础环境配置完成！"
print_info "下一步请上传你的项目代码到 /var/www/sentiment-analysis"
print_info "然后运行第二部分脚本来配置应用环境"

echo ""
echo "📝 接下来的步骤："
echo "1. 上传项目代码: scp -r sentiment-analysis-agent/ ec2-user@your-ip:/tmp/"
echo "2. 移动代码: sudo mv /tmp/sentiment-analysis-agent/* /var/www/sentiment-analysis/"
echo "3. 运行应用配置: sudo bash configure_app.sh"






