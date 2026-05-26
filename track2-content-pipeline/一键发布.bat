@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo ============================================
echo   一键发布 - 全平台
echo ============================================
echo.

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
