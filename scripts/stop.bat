@echo off
echo.
echo  ========================================
echo    Photo Pick - Stop Services
echo  ========================================
echo.

set backend_stopped=0
set frontend_stopped=0

:: Kill backend on port 8000
netstat -aon 2>nul | findstr ":8000.*LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000.*LISTENING"') do (
        taskkill /F /PID %%a >nul 2>&1
    )
    set backend_stopped=1
)

:: Kill frontend on port 5173
netstat -aon 2>nul | findstr ":5173.*LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5173.*LISTENING"') do (
        taskkill /F /PID %%a >nul 2>&1
    )
    set frontend_stopped=1
)

echo.
if %backend_stopped%==1 (
    echo  [OK] Backend stopped (port 8000)
) else (
    echo  [--] Backend was not running
)

if %frontend_stopped%==1 (
    echo  [OK] Frontend stopped (port 5173)
) else (
    echo  [--] Frontend was not running
)

echo.
echo  ----------------------------------------
if %backend_stopped%==1 if %frontend_stopped%==1 (
    echo    All services stopped successfully.
) else (
    echo    Done.
)
echo  ----------------------------------------
echo.
pause
