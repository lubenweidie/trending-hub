@echo off
chcp 65001 >nul
echo ========================================
echo   运行内容管线
echo ========================================
echo.

cd /d "%~dp0..\track2-content-pipeline"

echo [启动] 开始执行采集 -> 过滤 -> AI摘要 -> 生成 -> 校验...

python pipeline.py

if errorlevel 1 (
    echo.
    echo [FAIL] 管线执行失败
    pause
    exit /b 1
)

echo.
echo [OK] 管线执行完成，输出文件: output\index.html
pause
