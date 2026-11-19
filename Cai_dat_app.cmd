@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv
    if errorlevel 1 goto failed
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
".venv\Scripts\python.exe" setup_ocr.py
if errorlevel 1 goto failed
echo Cai dat thanh cong. Bam Mo_app.cmd de su dung.
pause
exit /b 0
:failed
echo Cai dat chua thanh cong. Can Python 3.10 tro len va ket noi Internet de tai thu vien.
pause
exit /b 1
