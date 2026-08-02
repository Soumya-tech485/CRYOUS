@echo off
cd /d "%~dp0"
echo === CRYOUS installer ===
python -m venv venv
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
python scripts\download_model.py
echo.
echo Install complete. Next: copy .env.example to .env, add a free API key, then run run.bat
pause