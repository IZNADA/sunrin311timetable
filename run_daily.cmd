@echo off
REM Ensure working directory is the repo root
cd /d %~dp0
REM Run daily flow via daemon entry
venv\Scripts\python.exe -m src.daemon --run-now
