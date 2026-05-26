﻿@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================
echo   设置定时任务 - 一键发布
echo ============================================
echo.
echo 输入多个执行时间，用空格分隔
echo 例如: 8:00 14:00 20:00
echo.

set /p TIMES=执行时间:

setlocal enabledelayedexpansion
set COUNT=0
set FAIL=0

for %%T in (%TIMES%) do (
    for /f "tokens=1,2 delims=:" %%H in ("%%T") do (
        set HR=00%%H
        set HR=!HR:~-2!
        set MN=00%%M
        set MN=!MN:~-2!
    )

    set TASK_NAME=一键发布-!HR!!MN!
    echo [创建] !TASK_NAME! — 每天 !HR!:!MN!

    schtasks /create /tn "!TASK_NAME!" /tr "\"%~dp0_定时启动.bat\"" /sc daily /st !HR!:!MN!:00 /f 2>nul
    if errorlevel 1 (
        echo   [FAIL] 请以管理员身份运行
        set /a FAIL+=1
    ) else (
        echo   [OK]
        set /a COUNT+=1
    )
)

echo.
echo ============================================
echo   完成：成功 !COUNT! 个，失败 !FAIL! 个
echo ============================================
echo.
echo 管理命令：
echo   查看所有： schtasks /query /fo list ^| findstr "一键发布"
echo   立即执行： schtasks /run /tn "一键发布-0800"
echo   删除指定： schtasks /delete /tn "一键发布-0800" /f
pause
