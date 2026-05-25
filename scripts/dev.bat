@echo off
echo.
echo  ========================================
echo    Photo Pick - Start Dev Servers
echo  ========================================
echo.

:: Check port 8000
netstat -aon 2>nul | findstr ":8000.*LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo  [!] Port 8000 is busy. Run stop.bat first.
    echo.
    pause
    exit /b 1
)

:: Check port 5173
netstat -aon 2>nul | findstr ":5173.*LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo  [!] Port 5173 is busy. Run stop.bat first.
    echo.
    pause
    exit /b 1
)

:: Check backend venv
if not exist "%~dp0..\backend\.venv\Scripts\activate.bat" (
    echo  [!] Backend venv not found. Please run:
    echo      cd backend
    echo      python -m venv .venv
    echo      .venv\Scripts\activate
    echo      pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

:: Start backend
echo  [...] Starting backend...
start "Photo Pick Backend" "%~dp0..\backend\start.bat"

timeout /t 4 /nobreak >nul

:: Start frontend
echo  [...] Starting frontend...
start "Photo Pick Frontend" "%~dp0..\frontend\start.bat"

timeout /t 2 /nobreak >nul

echo.
echo  [OK] All services started!
echo.
echo  ----------------------------------------
echo    Backend:  http://127.0.0.1:8000
echo    Frontend: http://127.0.0.1:5173
echo.
echo    Open http://localhost:5173 in browser
echo    Run stop.bat to stop services
echo  ----------------------------------------
echo.
pause
