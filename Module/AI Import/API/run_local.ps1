$ErrorActionPreference = "Stop"

$apiRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$moduleRoot = Split-Path -Parent $apiRoot
$repositoryRoot = Split-Path (Split-Path $moduleRoot -Parent) -Parent
$candidates = @(
    (Join-Path $repositoryRoot ".venv\Scripts\python.exe"),
    (Join-Path $moduleRoot "Train\.venv\Scripts\python.exe")
)
# Thêm Python cài trên máy làm phương án dự phòng
$candidates += @(Get-Command python.exe -All -ErrorAction SilentlyContinue |
    Where-Object { $_.Source -notlike "*WindowsApps*" } | ForEach-Object { $_.Source })

# Chọn Python đầu tiên chạy được và có đủ thư viện (.venv hỏng sẽ bị bỏ qua)
$python = $null
foreach ($candidate in $candidates) {
    if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) { continue }
    $ErrorActionPreference = "Continue"
    & $candidate -c "import torch, uvicorn, fastapi, openpyxl" 2>$null | Out-Null
    $ok = ($LASTEXITCODE -eq 0)
    $ErrorActionPreference = "Stop"
    if ($ok) { $python = $candidate; break }
}

if ([string]::IsNullOrWhiteSpace($python)) {
    throw "Không tìm thấy Python environment. Đã kiểm tra: $($candidates -join ', ')"
}

& $python -m uvicorn main:app --app-dir $apiRoot --host 127.0.0.1 --port 8010
