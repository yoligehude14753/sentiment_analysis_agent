#!/bin/bash

echo '=== 舆情分析系统完整启动脚本 ==='

# 检查虚拟环境
if [ ! -d 'venv' ]; then
    echo '创建虚拟环境...'
    python3 -m venv venv
fi

# 激活虚拟环境
echo '激活虚拟环境...'
source venv/bin/activate

# 创建必要目录
echo '创建必要目录...'
mkdir -p data exports logs

# 设置权限
echo '设置目录权限...'
chmod 755 data exports logs

# 检查数据库文件
if [ ! -f 'data/analysis_results.db' ]; then
    echo '数据库文件不存在，将在首次运行时自动创建'
fi

# 启动应用
echo '启动舆情分析系统...'
echo '访问地址: http://localhost:8000'
echo '管理界面: http://localhost:8000/config'
echo '按 Ctrl+C 停止服务'
echo '=========================================='

python main.py
