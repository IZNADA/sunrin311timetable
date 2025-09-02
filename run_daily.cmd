@echo off
REM Ensure working directory is the repo root
cd /d %~dp0
REM Run daily flow (test mode by default)
venv\Scripts\python.exe src\main_daily.py

