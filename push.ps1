Write-Host "Pushing Divya Trading Co website to GitHub..." -ForegroundColor Cyan
$git = if (Get-Command git -ErrorAction SilentlyContinue) { "git" } else { "$env:LOCALAPPDATA\Programs\MinGit\cmd\git.exe" }
& $git push -u origin main
Write-Host "Done!" -ForegroundColor Green
