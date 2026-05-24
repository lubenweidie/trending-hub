@echo off
chcp 65001 >nul
cd /d "%~dp0track2-content-pipeline"

echo.
echo ============================================
echo   百家号全自动发布
echo ============================================
echo.

REM 配置 API Key
set DEEPSEEK_API_KEY=sk-1ac3f874d1a8412fb1bf62e541591c98
set ARTICLE_LIMIT=1

REM 发布模式：默认存草稿(draft)，传 publish 则立即发布
set PUBLISH_MODE=draft
if "%1"=="publish" set PUBLISH_MODE=publish
if "%1"=="发" set PUBLISH_MODE=publish
echo   模式: %PUBLISH_MODE% (存草稿=安全 / publish=立即发布)
echo.

echo [1/2] 采集热点 + AI摘要 + 生成文章...
python pipeline.py
if errorlevel 1 (
    echo [FAIL] 文章生成失败
    pause
    exit /b 1
)

echo.
echo [2/2] 发布到百家号...
python baijiahao_publisher.py -m %PUBLISH_MODE%
if errorlevel 1 (
    echo [FAIL] 发布失败，请确认: 1^) Chrome已打开 2^) 已登录百家号 3^) 扩展已连接
    pause
    exit /b 1
)

echo.
echo ============================================
echo   完成！（模式: %PUBLISH_MODE%）
echo ============================================
pause
