@echo off
title QuantumShield Backend (Flask + VQE / ML)
echo Activating virtual environment...
cd /d "%~dp0"
call venv\Scripts\activate.bat
echo Starting Flask backend on port 5000...
python app.py
pause
