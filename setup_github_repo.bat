@echo off
chcp 65001 > nul
echo ==========================================
echo     情感分析系统 - GitHub仓库设置脚本
echo ==========================================
echo.

echo 请按照以下步骤设置GitHub远程仓库：
echo.
echo 1. 在GitHub上创建新仓库：
echo    - 访问：https://github.com/new
echo    - 仓库名称：sentiment-analysis-agent
echo    - 描述：智能情感分析代理系统 - 基于阿里云通义千问的多功能文本分析平台
echo    - 设置为公开或私有（根据需要）
echo    - 不要初始化README、.gitignore或LICENSE（我们已经有了）
echo.

echo 2. 创建完成后，复制仓库的HTTPS URL
echo    格式类似：https://github.com/yourusername/sentiment-analysis-agent.git
echo.

set /p REPO_URL="请输入您的GitHub仓库URL: "

if "%REPO_URL%"=="" (
    echo 错误：未提供仓库URL
    pause
    exit /b 1
)

echo.
echo 正在添加远程仓库...
git remote add origin %REPO_URL%

echo.
echo 正在推送到GitHub...
git branch -M main
git push -u origin main

if %ERRORLEVEL% equ 0 (
    echo.
    echo ✅ 成功！您的代码已上传到GitHub
    echo.
    echo 🔗 仓库地址：%REPO_URL%
    echo.
    echo 后续提交代码使用：
    echo    git add .
    echo    git commit -m "提交信息"
    echo    git push
) else (
    echo.
    echo ❌ 推送失败，可能的原因：
    echo 1. 仓库URL不正确
    echo 2. 需要GitHub身份验证
    echo 3. 网络连接问题
    echo.
    echo 请检查以上问题后重试
)

echo.
pause 