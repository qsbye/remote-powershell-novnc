# 编译打包脚本 - 带时间戳后缀
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outputName = "http_shell_cli_vnc_$timestamp.exe"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  HTTP Shell CLI + VNC 打包脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 确保依赖完整
Write-Host "[1/3] 整理依赖..." -ForegroundColor Yellow
go mod tidy
if ($LASTEXITCODE -ne 0) {
    Write-Host "依赖整理失败!" -ForegroundColor Red
    exit 1
}

# 编译 Windows 版本
Write-Host "[2/3] 编译 Windows 版本..." -ForegroundColor Yellow
go build -ldflags "-s -w" -o $outputName .
if ($LASTEXITCODE -ne 0) {
    Write-Host "编译失败!" -ForegroundColor Red
    exit 1
}

# 显示结果
$fileInfo = Get-Item $outputName
Write-Host "[3/3] 编译完成!" -ForegroundColor Green
Write-Host ""
Write-Host "输出文件: $outputName" -ForegroundColor Green
Write-Host "文件大小: $([math]::Round($fileInfo.Length / 1MB, 2)) MB" -ForegroundColor Green
Write-Host "修改时间: $($fileInfo.LastWriteTime)" -ForegroundColor Green
Write-Host ""
Write-Host "使用方式:" -ForegroundColor Cyan
Write-Host "  服务端: .\$outputName -role server -port 10022" -ForegroundColor Gray
Write-Host "  客户端: .\$outputName -role client -url http://<ip>:10022" -ForegroundColor Gray
