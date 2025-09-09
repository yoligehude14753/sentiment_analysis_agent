@echo off
chcp 65001 >nul
title JSON文件去重工具

echo.
echo ========================================
echo        JSON文件去重工具
echo ========================================
echo.

echo 请将需要去重的JSON文件拖拽到此窗口，然后按回车键
echo 或者直接输入文件路径，然后按回车键
echo.

set /p filepath="请输入JSON文件路径: "

if "%filepath%"=="" (
    echo 错误：未输入文件路径
    pause
    exit /b
)

echo.
echo 是否自动导入数据库？
echo 1. 是（默认）
echo 2. 否
echo.
set /p db_choice="请选择 (1/2): "

if "%db_choice%"=="2" (
    set auto_import=false
) else (
    set auto_import=true
)

echo.
echo 正在处理文件: %filepath%
echo 自动导入数据库: %auto_import%
echo.

python deduplicate_any_json.py "%filepath%" "" %auto_import%

echo.
echo 处理完成！按任意键退出...
pause >nul
