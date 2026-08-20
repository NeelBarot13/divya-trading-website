Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "Starting Divya Trading Co. Web Application..." -ForegroundColor Green
Write-Host "=========================================================" -ForegroundColor Cyan

if (Test-Path ".\venv\Scripts\python.exe") {
    .\venv\Scripts\python.exe app.py
} else {
    python app.py
}
