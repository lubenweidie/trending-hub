@echo off
chcp 65001 >nul
cd /d "%~dp0.."

echo ===============================================
echo   打开所有 Chrome Profile 窗口
echo ===============================================
echo.

python scripts/打开Chrome窗口.py
if errorlevel 1 (
    echo [FAIL] 打开 Chrome 窗口失败
    pause
    exit /b 1
)

echo.
echo [OK] 完成
pause
