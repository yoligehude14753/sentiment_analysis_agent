# JSON文件去重工具 - PowerShell版本
# 使用方法：右键点击此文件，选择"使用PowerShell运行"

param(
    [Parameter(Mandatory=$false)]
    [string]$InputFile = "",
    [Parameter(Mandatory=$false)]
    [bool]$AutoImportDatabase = $true
)

# 设置控制台编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "🚀 JSON文件去重工具" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Cyan
Write-Host ""

# 如果没有提供文件路径，让用户选择
if ([string]::IsNullOrEmpty($InputFile)) {
    Write-Host "请选择要处理的JSON文件..." -ForegroundColor Yellow
    
    # 创建文件选择对话框
    Add-Type -AssemblyName System.Windows.Forms
    $FileBrowser = New-Object System.Windows.Forms.OpenFileDialog
    $FileBrowser.Filter = "JSON文件 (*.json)|*.json|所有文件 (*.*)|*.*"
    $FileBrowser.Title = "选择要去重的JSON文件"
    
    if ($FileBrowser.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
        $InputFile = $FileBrowser.FileName
    } else {
        Write-Host "❌ 未选择文件，操作取消" -ForegroundColor Red
        Read-Host "按回车键退出"
        exit
    }
}

# 检查文件是否存在
if (-not (Test-Path $InputFile)) {
    Write-Host "❌ 文件不存在: $InputFile" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit
}

# 询问是否导入数据库
Write-Host "是否自动导入数据库？" -ForegroundColor Yellow
Write-Host "1. 是（默认）" -ForegroundColor Green
Write-Host "2. 否" -ForegroundColor Green
Write-Host ""

$dbChoice = Read-Host "请选择 (1/2)"
if ($dbChoice -eq "2") {
    $AutoImportDatabase = $false
}

Write-Host "📁 输入文件: $InputFile" -ForegroundColor Green
Write-Host "🔄 自动导入数据库: $($AutoImportDatabase ? '是' : '否')" -ForegroundColor Green
Write-Host ""

# 检查Python脚本是否存在
$ScriptPath = Join-Path $PSScriptRoot "deduplicate_any_json.py"
if (-not (Test-Path $ScriptPath)) {
    Write-Host "❌ 找不到去重脚本: $ScriptPath" -ForegroundColor Red
    Write-Host "请确保 deduplicate_any_json.py 文件在同一目录下" -ForegroundColor Yellow
    Read-Host "按回车键退出"
    exit
}

# 执行去重
try {
    Write-Host "🔄 正在执行去重操作..." -ForegroundColor Yellow
    
    # 构建参数
    $autoImportParam = if ($AutoImportDatabase) { "true" } else { "false" }
    $Result = python $ScriptPath $InputFile "" $autoImportParam
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ 去重操作完成！" -ForegroundColor Green
        
        # 查找生成的文件
        $OutputDir = Split-Path $InputFile
        $InputName = [System.IO.Path]::GetFileNameWithoutExtension($InputFile)
        $OutputFiles = Get-ChildItem -Path $OutputDir -Filter "*${InputName}_deduplicated_*.json" | Sort-Object LastWriteTime -Descending
        
        if ($OutputFiles.Count -gt 0) {
            $LatestOutput = $OutputFiles[0]
            Write-Host "📄 输出文件: $($LatestOutput.FullName)" -ForegroundColor Green
            Write-Host "📅 创建时间: $($LatestOutput.LastWriteTime)" -ForegroundColor Gray
            
            # 询问是否打开输出文件
            $OpenFile = Read-Host "是否打开输出文件？(y/n)"
            if ($OpenFile -eq 'y' -or $OpenFile -eq 'Y') {
                Start-Process $LatestOutput.FullName
            }
        }
        
        # 如果导入了数据库，显示相关信息
        if ($AutoImportDatabase) {
            Write-Host ""
            Write-Host "💾 数据已自动导入到数据库: data/analysis_results.db" -ForegroundColor Cyan
        }
    } else {
        Write-Host "❌ 去重操作失败" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ 执行过程中发生错误: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "按回车键退出..." -ForegroundColor Gray
Read-Host
