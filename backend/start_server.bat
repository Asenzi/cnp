@echo off
cd /d "f:\项目区\friends\backend"
call .venv\Scripts\activate.bat
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
