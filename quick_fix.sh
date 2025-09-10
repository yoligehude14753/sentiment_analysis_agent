#!/bin/bash
echo '=== 快速修复依赖包问题 ==='
echo '安装缺失的依赖包...'
pip install aiohttp httpx websockets
echo '依赖包安装完成！'
echo '现在可以重新启动应用:'
echo 'python3 main.py'
