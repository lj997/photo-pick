@echo off
cd /d "%~dp0"
echo.
echo  Photo Pick Frontend starting...
echo  URL: http://127.0.0.1:5173
echo  Press Ctrl+C to stop
echo.
if not exist "node_modules" (
    npm install
)
npm run dev
pause
