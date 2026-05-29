@echo off
chcp 65001 >nul
cd /d "%~dp0.."

REM 随机延迟，%1 为最大秒数（默认 900，即 15 分钟）
set MAX=%1
if "%MAX%"=="" set MAX=900
set /a DELAY=%RANDOM% %% %MAX%
echo [随机延迟] %DELAY% 秒（最大 %MAX% 秒）后开始发布...
timeout /t %DELAY% /nobreak >nul

set SCHEDULED=1
call "%~dp0一键发布.bat"
