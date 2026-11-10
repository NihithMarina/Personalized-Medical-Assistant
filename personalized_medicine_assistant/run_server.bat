@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" manage.py runserver
) else (
    "..\.venv\Scripts\python.exe" manage.py runserver
)
