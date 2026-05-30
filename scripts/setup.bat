进行@echo off
chcp 65001 >nul
echo ========================================
echo   环境安装
echo ========================================
echo.

cd /d "%~dp0..\track2-content-pipeline"

echo [1/2] 检查 Python...
python --version
if errorlevel 1 (
    echo [ERROR] 未找到 Python，请先安装 Python 3.9+
    pause
    exit /b 1
)

echo [2/2] 安装依赖...
pip install requests jinja2 beautifulsoup4

echo.
echo [OK] 环境准备完成
pause
