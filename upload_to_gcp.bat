@echo off
echo ==========================================
echo 🚀 上传舆情分析系统到GCP虚拟机
echo ==========================================

set VM_IP=35.209.254.98
set SSH_KEY="C:\Users\anyut\.ssh\google_compute_engine"
set USER=anyut

echo    查找最新的部署包...
for /f "delims=" %%i in ('dir /b /o-d sentiment-analysis-gcp-linux-*.tar.gz 2^>nul') do set PACKAGE=%%i

if "%PACKAGE%"=="" (
    echo ❌ 未找到部署包，请先运行打包脚本
    pause
    exit /b 1
)

echo    找到部署包: %PACKAGE%

echo    上传到GCP虚拟机...
scp -i %SSH_KEY% %PACKAGE% %USER%@%VM_IP%:~/

if %errorlevel% neq 0 (
    echo ❌ 上传失败
    pause
    exit /b 1
)

echo ✅ 上传完成！
echo 🚀 连接到虚拟机进行部署...
ssh -i %SSH_KEY% %USER%@%VM_IP%