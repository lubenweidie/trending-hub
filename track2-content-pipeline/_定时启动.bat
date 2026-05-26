@echo off
chcp 65001 >nul
cd /d "%~dp0"

REM 随机延迟 0-900 秒（0-15分钟）
set /a DELAY=%RANDOM% %% 900
echo [随机延迟] %DELAY% 秒后开始发布...
timeout /t %DELAY% /nobreak >nul

call "%~dp0一键发布.bat"
