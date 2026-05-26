﻿@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo ============================================
echo   一键发布 - 全平台
echo ============================================
echo.

echo [启动] 打开 Chrome 浏览器...
set CHROME=
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" set CHROME=C:\Program Files\Google\Chrome\Application\chrome.exe
if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" set CHROME=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe
if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" set CHROME=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe
if defined CHROME (start "" "%CHROME%") else (start "" chrome.exe)
echo [等待] 等待浏览器就绪（5秒）...
timeout /t 5 /nobreak >nul

python publish.py -p toutiao,baijiahao --publish
if errorlevel 1 (
    echo [FAIL] 发布失败
    pause
    exit /b 1
)

echo.
echo ============================================
echo   全部完成！
echo ============================================
pause
