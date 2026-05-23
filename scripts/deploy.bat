@echo off
chcp 65001 >nul
echo ========================================
echo   部署到 GitHub Pages
echo ========================================
echo.

cd /d "%~dp0.."

if not exist "track2-content-pipeline\output\index.html" (
    echo [ERROR] 未找到 output\index.html，请先运行 run_pipeline.bat
    pause
    exit /b 1
)

echo [1/3] 切换到 gh-pages 分支...
git checkout gh-pages 2>nul || git checkout --orphan gh-pages

echo [2/3] 部署 HTML...
git rm -rf --cached . 2>nul
del /q * 2>nul
for /d %%d in (*) do rmdir /s /q "%%d" 2>nul
copy /y "track2-content-pipeline\output\index.html" . >nul
git add index.html

echo [3/3] 提交 & 推送...

for /f "tokens=2 delims==" %%i in ('wmic os get localdatetime /value') do set dt=%%i
set commit_date=%dt:~0,4%-%dt:~4,2%-%dt:~6,2%
set commit_time=%dt:~8,2%:%dt:~10,2%

git config user.name "TrendBot"
git config user.email "bot@trends.local"
git commit -m "Update: %commit_date% %commit_time% BJT"
git push origin gh-pages --force

if errorlevel 1 (
    echo.
    echo [FAIL] 部署失败，请确认已配置 Git 远程仓库
    pause
    exit /b 1
)

echo.
echo [OK] 部署完成: https://lubenweidie.github.io/trending-hub/
pause
