@echo off
color 0A
echo ================================================
echo    TheZ's Web Crawler V2 Setup
echo ================================================
echo.
echo [*] Initializing setup sequence...
timeout /t 1 /nobreak >nul

:: Check for pip
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] Installing pip...
    python -m ensurepip --default-pip
)

echo [*] Upgrading pip to latest version...
python -m pip install --upgrade pip

echo [*] Installing packages...
echo.
pip install requests
pip install beautifulsoup4
pip install aiohttp
pip install asyncio
pip install customtkinter
echo.
echo ================================================
echo          Installation Complete! 
echo ================================================
echo [+] Web Crawler is ready for action!
echo [+] Created by TheZ
echo [+] Launch crawler_V2.py to begin
echo ================================================
echo.
color 0A
pause
