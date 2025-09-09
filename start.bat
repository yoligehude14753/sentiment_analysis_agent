@echo off
chcp 65001 >nul
echo ========================================
echo 舆情分析Agent系统启动脚本
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python，请先安装Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python已安装
echo.

REM 检查依赖是否安装
echo 🔍 检查依赖包...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo 📦 安装依赖包...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ 依赖安装失败
        pause
        exit /b 1
    )
    echo ✅ 依赖安装完成
) else (
    echo ✅ 依赖包已安装
)

echo.
echo 🚀 启动系统...
echo 系统将在 http://localhost:8000 启动
echo 按 Ctrl+C 停止服务
echo.

REM 启动系统
python main.py

pause 