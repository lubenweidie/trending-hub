@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo ============================================
echo   一键发布 - 今日头条
echo ============================================
echo.

python publish.py -p toutiao --publish
if errorlevel 1 (
    echo [FAIL] 今日头条发布失败
    pause
    exit /b 1
)

echo.
echo ============================================
echo   一键发布 - 百家号
echo ============================================
echo.

python publish.py -p baijiahao --publish
if errorlevel 1 (
    echo [FAIL] 百家号发布失败
    pause
    exit /b 1
)

echo.
echo ============================================
echo   全部完成！
echo ============================================
pause
