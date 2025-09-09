#!/bin/bash

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

echo "=========================================="
echo "    情感分析系统 - GitHub仓库设置脚本"
echo "=========================================="
echo ""

print_info "请按照以下步骤设置GitHub远程仓库："
echo ""
echo "1. 在GitHub上创建新仓库："
echo "   - 访问：https://github.com/new"
echo "   - 仓库名称：sentiment-analysis-agent"
echo "   - 描述：智能情感分析代理系统 - 基于阿里云通义千问的多功能文本分析平台"
echo "   - 设置为公开或私有（根据需要）"
echo "   - 不要初始化README、.gitignore或LICENSE（我们已经有了）"
echo ""

echo "2. 创建完成后，复制仓库的HTTPS URL"
echo "   格式类似：https://github.com/yourusername/sentiment-analysis-agent.git"
echo ""

read -p "请输入您的GitHub仓库URL: " REPO_URL

if [ -z "$REPO_URL" ]; then
    print_error "未提供仓库URL"
    exit 1
fi

echo ""
print_info "正在添加远程仓库..."
git remote add origin "$REPO_URL"

echo ""
print_info "正在推送到GitHub..."
git branch -M main
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    print_success "成功！您的代码已上传到GitHub"
    echo ""
    echo "🔗 仓库地址：$REPO_URL"
    echo ""
    print_info "后续提交代码使用："
    echo "   git add ."
    echo "   git commit -m \"提交信息\""
    echo "   git push"
else
    echo ""
    print_error "推送失败，可能的原因："
    echo "1. 仓库URL不正确"
    echo "2. 需要GitHub身份验证"
    echo "3. 网络连接问题"
    echo ""
    print_warning "请检查以上问题后重试"
fi

echo "" 