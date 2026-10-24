@echo off
title Divya Trading Co - Server Deployment
echo ========================================================
echo  Deploying Latest Changes to divyatradingco.com
echo ========================================================
echo.
set "PATH=%LOCALAPPDATA%\Programs\MinGit\cmd;%PATH%"

echo 1. Ensuring local changes are pushed to GitHub...
git push origin main

echo.
echo 2. Syncing code to live Ubuntu server (157.20.190.212)...
.\venv\Scripts\python.exe deploy_to_server.py

pause
