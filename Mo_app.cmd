@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" "%~dp0app.py"
) else (
    echo Hay chay Cai_dat_app.cmd truoc khi mo ung dung.
    pause
)
