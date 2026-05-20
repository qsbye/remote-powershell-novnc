@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM 编译打包脚本 - 带时间戳后缀
for /f "tokens=2-7 delims=/:- " %%a in ('echo %date% %time%') do (
    set timestamp=%%c%%a%%b_%%d%%e%%f
)
set timestamp=%timestamp: =0%
set outputName=http_shell_cli_vnc_%timestamp%.exe

echo ========================================
echo   HTTP Shell CLI + VNC 打包脚本
echo ========================================
echo.

echo [1/3] 整理依赖...
go mod tidy
if %errorlevel% neq 0 (
    echo 依赖整理失败!
    exit /b 1
)

echo [2/3] 编译 Windows 版本...
go build -ldflags "-s -w" -o %outputName% .
if %errorlevel% neq 0 (
    echo 编译失败!
    exit /b 1
)

echo [3/3] 编译完成!
echo.
echo 输出文件: %outputName%
for %%F in (%outputName%) do echo 文件大小: %%~zF 字节
echo.
echo 使用方式:
echo   服务端: %outputName% -role server -port 10022
echo   客户端: %outputName% -role client -url http://^<ip^>:10022

pause
