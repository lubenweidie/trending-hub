@echo off
chcp 65001 >nul
cd /d "%~dp0.."
setlocal enabledelayedexpansion

:MENU
cls
echo ============================================
echo   定时任务管理
echo ============================================
echo.
echo   [1] 同步定时任务（从 config\schedule.conf）
echo   [2] 查看所有定时任务
echo   [3] 删除所有定时任务
echo   [0] 退出
echo.
set /p CHOICE=请输入选项: 

if "%CHOICE%"=="1" goto SYNC
if "%CHOICE%"=="2" goto LIST
if "%CHOICE%"=="3" goto DELETE
if "%CHOICE%"=="0" exit /b 0
echo   无效选项，请重新输入
timeout /t 1 >nul
goto MENU

:SYNC
echo.
if not exist "%~dp0..\config\schedule.conf" (
    echo   [FAIL] config\schedule.conf 不存在
    pause
    goto MENU
)
echo.
echo 先清理旧任务...
set CLEAN_COUNT=0
for /f "tokens=1" %%N in ('schtasks /query /fo TABLE /nh ^| findstr /c:"一键发布-"') do (
    schtasks /delete /tn "%%N" /f 2>nul
    if not errorlevel 1 set /a CLEAN_COUNT+=1
)
echo 已清理 !CLEAN_COUNT! 个旧任务
echo.
echo 按 config\schedule.conf 创建新任务...
echo.
set SYNC_OK=0
set SYNC_FAIL=0
for /f "usebackq tokens=1,2 delims= " %%T in ("%~dp0..\config\schedule.conf") do (
    set LINE=%%T
    if not "!LINE:~0,1!"=="#" (
        for /f "tokens=1,2 delims=:" %%H in ("%%T") do (
            set HR=00%%H
            set HR=!HR:~-2!
            set MN=00%%I
            set MN=!MN:~-2!
        )
        set DLY=%%U
        if "!DLY!"=="" set DLY=15
        set /a MAX_SEC=!DLY! * 60
        set TASK_NAME=一键发布-!HR!!MN!
        echo [同步] !TASK_NAME! — 每天 !HR!:!MN!（随机 0~!DLY! 分钟）
        schtasks /create /tn "!TASK_NAME!" /tr "\"%~dp0_随机延时.bat\" !MAX_SEC!" /sc daily /st !HR!:!MN!:00 /f 2>nul
        if errorlevel 1 (
            echo   [FAIL] 请以管理员身份运行
            set /a SYNC_FAIL+=1
        ) else (
            echo   [OK]
            set /a SYNC_OK+=1
        )
    )
)
echo.
echo ============================================
echo   同步完成：成功 !SYNC_OK! 个，失败 !SYNC_FAIL! 个
echo ============================================
echo.
pause
goto MENU

:LIST
echo.
echo ============================================
echo   当前定时任务列表
echo ============================================
echo.
set TASK_COUNT=0
for /f "tokens=1" %%N in ('schtasks /query /fo TABLE /nh ^| findstr /c:"一键发布-"') do (
    set TASK_NAME=%%N
    set /a TASK_COUNT+=1
    for /f "tokens=2 delims=:" %%X in ('schtasks /query /fo LIST /tn "!TASK_NAME!" ^| findstr "Next Run Time"') do (
        echo   !TASK_NAME! — 下次运行:%%X
    )
    if errorlevel 1 echo   !TASK_NAME!
)
if !TASK_COUNT! equ 0 (
    echo   没有找到任何"一键发布-*"定时任务
)
echo.
echo 共 !TASK_COUNT! 个任务
echo.
pause
goto MENU

:DELETE
echo.
echo ============================================
echo   删除所有定时任务
echo ============================================
echo.
set /p CONFIRM=确认删除所有"一键发布-*"定时任务? [y/N]:
if /i not "%CONFIRM%"=="y" (
    echo   已取消
    pause
    goto MENU
)
echo.
set DEL_OK=0
set DEL_FAIL=0
for /f "tokens=1" %%N in ('schtasks /query /fo TABLE /nh ^| findstr /c:"一键发布-"') do (
    set TASK_NAME=%%N
    echo [删除] !TASK_NAME!
    schtasks /delete /tn "!TASK_NAME!" /f 2>nul
    if errorlevel 1 (
        echo   [FAIL]
        set /a DEL_FAIL+=1
    ) else (
        echo   [OK]
        set /a DEL_OK+=1
    )
)
if !DEL_OK! equ 0 if !DEL_FAIL! equ 0 (
    echo   没有找到任何"一键发布-*"定时任务
)
echo.
echo ============================================
echo   删除完成：成功 !DEL_OK! 个，失败 !DEL_FAIL! 个
echo ============================================
echo.
pause
goto MENU
