#!/bin/bash

HOST=$1
KEY_FILE=$2

echo "🔍 测试SSH连接到 $HOST..."

# 设置密钥权限
chmod 600 "$KEY_FILE"

# 尝试连接
ssh -i "$KEY_FILE" -o ConnectTimeout=30 -o StrictHostKeyChecking=no ec2-user@$HOST "echo '✅ SSH连接成功!'; uptime"

if [ $? -eq 0 ]; then
    echo "✅ SSH连接测试成功!"
else
    echo "❌ SSH连接失败"
    echo "请检查："
    echo "1. EC2实例是否完全启动（等待2-3分钟）"
    echo "2. 安全组是否正确配置SSH端口22"
    echo "3. 密钥文件是否正确"
fi






