@echo off
REM Ensure working directory is the repo root
cd /d %~dp0
REM Run update flow (checks for changes)
venv\Scripts\python.exe src\main_update.py

