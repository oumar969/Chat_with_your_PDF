@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Python-miljoe mangler. Se README.md for installation.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" -m streamlit run app.py --server.address localhost --browser.gatherUsageStats false
pause
