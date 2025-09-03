@echo off
REM Ensure working directory is the repo root
cd /d %~dp0
REM Run update flow using daemon (no separate update entry)
venv\Scripts\python.exe -m src.daemon --run-now
