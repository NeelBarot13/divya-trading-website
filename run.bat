@echo off
title Divya Trading Co. Website Server
echo =========================================================
echo Starting Divya Trading Co. Web Application...
echo =========================================================
if exist venv\Scripts\python.exe (
    venv\Scripts\python.exe app.py
) else (
    python app.py
)
pause
