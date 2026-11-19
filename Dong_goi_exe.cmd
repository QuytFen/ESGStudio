@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" goto failed
".venv\Scripts\python.exe" -m pip install "pyinstaller>=6.16,<7"
if errorlevel 1 goto failed
".venv\Scripts\python.exe" setup_ocr.py
if errorlevel 1 goto failed
".venv\Scripts\python.exe" build_exe.py %1
if errorlevel 1 goto failed
echo Thanh cong: dist\ESGStudio\ESGStudio.exe
if /I "%~1"=="onefile" echo Ban mot file: dist\ESGStudio.exe
echo Khi chuyen may, sao chep nguyen thu muc dist\ESGStudio.
pause
exit /b 0
:failed
echo Dong goi chua thanh cong. Xem loi phia tren.
pause
exit /b 1
