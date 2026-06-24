@echo off
cd /d "%~dp0"

echo Checking python path...
where python
echo.
echo If the path above does NOT contain .venv - stop now (Ctrl+C)
echo and run this from PyCharm terminal instead.
echo.
pause

echo Checking PyInstaller...
python -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    python -m pip install pyinstaller
)

echo.
echo Building exe...
python -m PyInstaller --noconfirm --onefile --windowed --name "Dakimakury" --icon "icons\app_icon.ico" --add-data "dakimakury.xlsx;." --add-data "icons;icons" --add-data "images;images" main.py

if exist "dist\Dakimakury.exe" (
    echo.
    echo ===========================================
    echo SUCCESS! File is at dist\Dakimakury.exe
    echo ===========================================
) else (
    echo.
    echo ===========================================
    echo ERROR: exe was not created. See messages above.
    echo ===========================================
)
pause
