@echo off
setlocal enabledelayedexpansion

:: Set the root directory of the project
set "ROOT_DIR=%~dp0.."

:: Set colors and clear screen
color 0A
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
echo    Building Nikke OCR...
echo.

:: Check if virtual environment exists
if not exist "%ROOT_DIR%\.venv\Scripts\activate.bat" (
    echo Virtual environment not found. Please run setup script first.
    goto :error
)

:: Activate virtual environment
call "%ROOT_DIR%\.venv\Scripts\activate.bat"
if errorlevel 1 (
    echo Failed to activate virtual environment.
    goto :error
)

:: Install requirements
echo Installing requirements...
pip install -r "%ROOT_DIR%\requirements\dev.txt" -r "%ROOT_DIR%\requirements\prod.txt" >nul 2>&1
if errorlevel 1 (
    echo Failed to install requirements.
    goto :error
)

:: Delete previous build files
echo Deleting previous build files...
rmdir /s /q "%ROOT_DIR%\dist" >nul 2>&1
rmdir /s /q "%ROOT_DIR%\build" >nul 2>&1


:: Build with PyInstaller
echo Building with PyInstaller...
pyinstaller --clean "%ROOT_DIR%\nikke_ocr.spec" >nul 2>&1
if errorlevel 1 (
    echo Failed to build with PyInstaller.
    goto :error
)

:: Loading animation
for /L %%i in (1,1,10) do (
    cls
    echo.
    echo    _   _ _ _    _
    echo   ^| \ ^| (_) ^| _^| ^| _____
    echo   ^|  \^| ^| ^| ^|/ / ^|/ / _ \
    echo   ^| ^|\  ^| ^|   <^|   <  __/
    echo   ^|_^| \_^|_^|_^|\_\_^|\_\___ ^|
    echo      Goddess of Victory
    echo.
    echo    Building Nikke OCR...
    echo.
    echo    [!%%%%%%%   ] Building...
    ping -n 2 127.0.0.1 >nul
)

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
echo    Nikke OCR build complete!
echo    The executable can be found in the 'dist' folder.
echo.
goto :end

:error
echo.
echo An error occurred during the build process.
echo Please check the error messages above.

:end
pause
endlocal
