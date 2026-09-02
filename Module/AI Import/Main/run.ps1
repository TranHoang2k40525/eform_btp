$ErrorActionPreference = 'Stop'
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $scriptRoot
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    throw 'Chưa có môi trường .venv. Xem README.md để cài đặt.'
}
& '.venv\Scripts\python.exe' -m uvicorn ai_import.api:app --host 127.0.0.1 --port 8010

