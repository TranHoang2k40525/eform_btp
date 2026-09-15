$ErrorActionPreference = "Stop"

$apiRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$moduleRoot = Split-Path -Parent $apiRoot
$python = Join-Path $moduleRoot "Train\.venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw "Không tìm thấy môi trường Python tại $python. Hãy chạy notebook train.ipynb trước."
}

& $python -m uvicorn main:app --app-dir $apiRoot --host 127.0.0.1 --port 8010

