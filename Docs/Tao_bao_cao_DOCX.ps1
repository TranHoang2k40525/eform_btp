$ErrorActionPreference = "Stop"

$docsRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $docsRoot
$pythonVenv = Join-Path $projectRoot ".venv\Scripts\python.exe"
$scriptPath = Join-Path $projectRoot "generate_reports_docx.py"

Write-Host "=========================================================="
Write-Host "   TAO BAO CAO THUC TAP DOCX (TUAN 8, 9, 10 & TONG HOP)   "
Write-Host "=========================================================="

if (Test-Path -LiteralPath $pythonVenv) {
    Write-Host "Khoi chay Python tu moi truong: $pythonVenv"
    & $pythonVenv $scriptPath
} else {
    Write-Host "Khoi chay Python tu moi truong he thong..."
    python $scriptPath
}

if ($LASTEXITCODE -ne 0) {
    throw "Co loi xay ra khi tao file bao cao DOCX."
}

Write-Host ""
Write-Host "Hoan tat tao cac bao cao thuc tap chuan muc:"
Write-Host " - Docs\Tuan 8\Bao cao thuc tap tuan 8.docx"
Write-Host " - Docs\Tuan 9\Bao cao thuc tap tuan 9.docx"
Write-Host " - Docs\Tuan 10\Bao cao thuc tap tuan 10.docx"
Write-Host " - Docs\Bao cao tong hop thuc tap tuan 8-10.docx"
Write-Host ""
