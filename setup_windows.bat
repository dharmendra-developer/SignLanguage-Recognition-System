@echo off
setlocal
cd /d "%~dp0"

echo ==================================================
echo  SignVoice AI - Windows setup
echo ==================================================

where py >nul 2>nul
if errorlevel 1 (
    echo ERROR: Python launcher "py" was not found.
    echo Install Python 3.10, 3.11, or 3.12 and enable "Add Python to PATH".
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    py -3.12 -m venv .venv
    if errorlevel 1 py -3.11 -m venv .venv
    if errorlevel 1 py -3.10 -m venv .venv
)

if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Could not create the Python virtual environment.
    pause
    exit /b 1
)

echo Installing or updating dependencies...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo Setup failed. Review the dependency error above.
    pause
    exit /b 1
)

echo.
echo Setup complete.
echo Starting SignVoice AI...
call start_signvoice.bat
