@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Missing .venv. Please run dev-up.ps1 first, or create it with:
  echo py -3.11 -m venv .venv
  exit /b 1
)
".venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
