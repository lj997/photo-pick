@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
echo.
echo  Photo Pick Backend starting...
echo  URL: http://127.0.0.1:8000
echo  Press Ctrl+C to stop
echo.
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
pause
