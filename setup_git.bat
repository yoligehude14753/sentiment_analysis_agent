@echo off
chcp 65001 >nul
echo ========================================
echo      Git版本管理自动化设置脚本
echo ========================================
echo.

REM 检查Git是否安装
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Git未安装，请先安装Git：
    echo    https://git-scm.com/download/win
    echo.
    pause
    exit /b 1
)

echo ✅ Git已安装
git --version
echo.

REM 检查是否已经是Git仓库
if exist ".git" (
    echo ℹ️  已存在Git仓库，跳过初始化
) else (
    echo 🔄 初始化Git仓库...
    git init
    if %errorlevel% neq 0 (
        echo ❌ Git初始化失败
        pause
        exit /b 1
    )
    echo ✅ Git仓库初始化成功
)
echo.

REM 检查Git用户配置
for /f "tokens=*" %%i in ('git config --global user.name 2^>nul') do set username=%%i
for /f "tokens=*" %%i in ('git config --global user.email 2^>nul') do set useremail=%%i

if "%username%"=="" (
    echo ⚠️  Git用户名未设置
    set /p username="请输入您的用户名: "
    git config --global user.name "%username%"
    echo ✅ 用户名设置完成
) else (
    echo ℹ️  当前用户名: %username%
)

if "%useremail%"=="" (
    echo ⚠️  Git邮箱未设置
    set /p useremail="请输入您的邮箱: "
    git config --global user.email "%useremail%"
    echo ✅ 邮箱设置完成
) else (
    echo ℹ️  当前邮箱: %useremail%
)
echo.

REM 添加所有文件
echo 🔄 添加项目文件到Git...
git add .
if %errorlevel% neq 0 (
    echo ❌ 文件添加失败
    pause
    exit /b 1
)
echo ✅ 文件添加成功
echo.

REM 进行初始提交
echo 🔄 进行初始提交...
git commit -m "feat: 初始化多Agent情感分析系统项目

- 添加企业识别Agent功能
- 添加标签分类Agents（14个维度）
- 添加情感分析Agent（5级分类）
- 完善Web界面和API接口
- 配置数据库存储和管理
- 添加批量处理和导出功能
- 建立完整的项目文档体系"

if %errorlevel% neq 0 (
    echo ❌ 初始提交失败
    pause
    exit /b 1
)
echo ✅ 初始提交成功
echo.

REM 创建develop分支
echo 🔄 创建develop分支...
git checkout -b develop
if %errorlevel% neq 0 (
    echo ❌ develop分支创建失败
    pause
    exit /b 1
)
echo ✅ develop分支创建成功
echo.

REM 切回main分支
echo 🔄 切换到main分支...
git checkout main
if %errorlevel% neq 0 (
    echo ❌ 切换到main分支失败
    pause
    exit /b 1
)
echo ✅ 已切换到main分支
echo.

echo ========================================
echo           设置完成！
echo ========================================
echo.
echo 📋 下一步操作：
echo 1. 在GitHub上创建新仓库 'sentiment-analysis-agent'
echo 2. 运行以下命令连接远程仓库：
echo.
echo    git remote add origin https://github.com/您的用户名/sentiment-analysis-agent.git
echo    git push -u origin main
echo    git push -u origin develop
echo.
echo 3. 查看详细说明：GIT_SETUP_GUIDE.md
echo.
echo 🎉 Git版本管理设置完成！
echo.
pause


