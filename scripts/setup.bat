@echo off
setlocal enabledelayedexpansion

:: Set the root directory of the project
set "ROOT_DIR=%~dp0.."

:: Set colors and clear screen
color 0B
cls

:: Nikke: Goddess of Victory ASCII Art
echo.
echo    _   _ _ _    _
echo   ^| \ ^| (_) ^| _^| ^| _____
echo   ^|  \^| ^| ^| ^|/ / ^|/ / _ \
echo   ^| ^|\  ^| ^|   <^|   <  __/
echo   ^|_^| \_^|_^|_^|\_\_^|\_\___ ^|
echo      Goddess of Victory
echo.
echo    Setting up Nikke OCR...
echo.

:: Function for animated waiting
:wait_animation
set "animation=\|/-"
set /a "index=0"
:loop
    set /a "index+=1"
    set /a "index%%=4"
    <nul set /p ".=!animation:~%index%,1!" <nul
    ping -n 2 127.0.0.1 >nul
    if not exist "%temp%\stop_animation" goto loop
del "%temp%\stop_animation" 2>nul
echo.
goto :eof

:: Check if Python is installed
echo Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH. Please install Python 3.9 or later and try again.
    goto :error
)
python --version
echo.

:: Create virtual environment
if not exist "%ROOT_DIR%\.venv" (
    echo Creating virtual environment...
    start /b "" cmd /c "python -m venv "%ROOT_DIR%\.venv" 2>nul && echo. > "%temp%\stop_animation""
    call :wait_animation
) else (
    echo Virtual environment already exists.
)

:: Activate virtual environment
echo Activating virtual environment...
call "%ROOT_DIR%\.venv\Scripts\activate.bat"
if %errorlevel% neq 0 (
    echo Failed to activate virtual environment.
    goto :error
)

:: Upgrade pip
echo Upgrading pip...
start /b "" cmd /c "python -m pip install --upgrade pip >nul 2>&1 && echo. > "%temp%\stop_animation""
call :wait_animation

:: Install requirements
echo Installing requirements...
start /b "" cmd /c "pip install -r "%ROOT_DIR%\requirements\dev.txt" -r "%ROOT_DIR%\requirements\prod.txt" >nul 2>&1 && echo. > "%temp%\stop_animation""
call :wait_animation

:: Install PyInstaller
echo Installing PyInstaller...
start /b "" cmd /c "pip install pyinstaller >nul 2>&1 && echo. > "%temp%\stop_animation""
call :wait_animation

:: Success message
cls
echo.
echo    _   _ _ _    _
echo   ^| \ ^| (_) ^| _^| ^| _____
echo   ^|  \^| ^| ^| ^|/ / ^|/ / _ \
echo   ^| ^|\  ^| ^|   <^|   <  __/
echo   ^|_^| \_^|_^|_^|\_\_^|\_\___ ^|
echo      Goddess of Victory
echo.
echo    Nikke OCR setup complete!
echo.
echo To activate the virtual environment, run:
echo %ROOT_DIR%\.venv\Scripts\activate
echo.
echo To build the project locally, run:
echo %ROOT_DIR%\scripts\build.bat
echo.
goto :end

:error
echo.
echo An error occurred during the setup process.
echo Please check the error messages above.

:end
echo Press any key to exit...
pause >nul
endlocal
