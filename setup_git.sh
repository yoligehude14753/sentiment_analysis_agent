#!/bin/bash
# Git版本管理自动化设置脚本 (Linux/Mac版本)

set -e  # 遇到错误立即退出

echo "========================================"
echo "     Git版本管理自动化设置脚本"
echo "========================================"
echo

# 检查Git是否安装
if ! command -v git &> /dev/null; then
    echo "❌ Git未安装，请先安装Git："
    echo "   Ubuntu/Debian: sudo apt-get install git"
    echo "   CentOS/RHEL: sudo yum install git"
    echo "   macOS: brew install git"
    echo
    exit 1
fi

echo "✅ Git已安装"
git --version
echo

# 检查是否已经是Git仓库
if [ -d ".git" ]; then
    echo "ℹ️  已存在Git仓库，跳过初始化"
else
    echo "🔄 初始化Git仓库..."
    git init
    echo "✅ Git仓库初始化成功"
fi
echo

# 检查Git用户配置
username=$(git config --global user.name 2>/dev/null || echo "")
useremail=$(git config --global user.email 2>/dev/null || echo "")

if [ -z "$username" ]; then
    echo "⚠️  Git用户名未设置"
    read -p "请输入您的用户名: " username
    git config --global user.name "$username"
    echo "✅ 用户名设置完成"
else
    echo "ℹ️  当前用户名: $username"
fi

if [ -z "$useremail" ]; then
    echo "⚠️  Git邮箱未设置"
    read -p "请输入您的邮箱: " useremail
    git config --global user.email "$useremail"
    echo "✅ 邮箱设置完成"
else
    echo "ℹ️  当前邮箱: $useremail"
fi
echo

# 添加所有文件
echo "🔄 添加项目文件到Git..."
git add .
echo "✅ 文件添加成功"
echo

# 进行初始提交
echo "🔄 进行初始提交..."
git commit -m "feat: 初始化多Agent情感分析系统项目

- 添加企业识别Agent功能
- 添加标签分类Agents（14个维度）
- 添加情感分析Agent（5级分类）
- 完善Web界面和API接口
- 配置数据库存储和管理
- 添加批量处理和导出功能
- 建立完整的项目文档体系"

echo "✅ 初始提交成功"
echo

# 创建develop分支
echo "🔄 创建develop分支..."
git checkout -b develop
echo "✅ develop分支创建成功"
echo

# 切回main分支
echo "🔄 切换到main分支..."
git checkout main
echo "✅ 已切换到main分支"
echo

echo "========================================"
echo "          设置完成！"
echo "========================================"
echo
echo "📋 下一步操作："
echo "1. 在GitHub上创建新仓库 'sentiment-analysis-agent'"
echo "2. 运行以下命令连接远程仓库："
echo
echo "   git remote add origin https://github.com/您的用户名/sentiment-analysis-agent.git"
echo "   git push -u origin main"
echo "   git push -u origin develop"
echo
echo "3. 查看详细说明：GIT_SETUP_GUIDE.md"
echo
echo "🎉 Git版本管理设置完成！"
echo


