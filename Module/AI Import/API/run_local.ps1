$ErrorActionPreference = "Stop"

$apiRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$moduleRoot = Split-Path -Parent $apiRoot
$repositoryRoot = Split-Path (Split-Path $moduleRoot -Parent) -Parent
$candidates = @(
    (Join-Path $repositoryRoot ".venv\Scripts\python.exe"),
    (Join-Path $moduleRoot "Train\.venv\Scripts\python.exe")
)
$python = $candidates | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1

if ([string]::IsNullOrWhiteSpace($python)) {
    throw "Không tìm thấy Python environment. Đã kiểm tra: $($candidates -join ', ')"
}

& $python -m uvicorn main:app --app-dir $apiRoot --host 127.0.0.1 --port 8010
