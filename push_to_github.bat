@echo off
echo Pushing Divya Trading Co website to GitHub...
set "PATH=%LOCALAPPDATA%\Programs\MinGit\cmd;%PATH%"
git push -u origin main
echo Done!
pause
