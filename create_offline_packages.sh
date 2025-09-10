#!/bin/bash

# 创建离线Python依赖包脚本

echo "=========================================="
echo "📦 创建离线Python依赖包"
echo "=========================================="

# 创建依赖包目录
mkdir -p offline_packages
cd offline_packages

# 下载所有依赖包
echo "📥 下载Python依赖包..."
pip download -r ../requirements.txt --dest .

# 创建安装脚本
echo "   创建离线安装脚本..."
cat > install_offline.sh << 'EOF'
#!/bin/bash

# 离线安装Python依赖

echo "=========================================="
echo "   离线安装Python依赖"
echo "=========================================="

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建Python虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 升级pip
echo "⬆️ 升级pip..."
pip install --upgrade pip

# 离线安装依赖
echo "📥 离线安装依赖包..."
pip install --no-index --find-links . -r requirements.txt

echo "✅ 离线安装完成！"
EOF

chmod +x install_offline.sh

# 复制requirements.txt
cp ../requirements.txt .

echo "✅ 离线依赖包创建完成！"
echo "📁 目录: offline_packages/"
echo "📦 包含所有依赖包和安装脚本"