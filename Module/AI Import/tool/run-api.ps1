$ErrorActionPreference = 'Stop'

$toolRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$runtimeRoot = Join-Path $toolRoot 'runtime'
$searchRoot = $toolRoot
$pythonPath = $null

while ($searchRoot) {
    $candidate = Join-Path $searchRoot '.venv\Scripts\python.exe'
    if (Test-Path -LiteralPath $candidate -PathType Leaf) {
        $pythonPath = (Resolve-Path -LiteralPath $candidate).Path
        break
    }

    $parent = Split-Path -Parent $searchRoot
    if (-not $parent -or $parent -eq $searchRoot) {
        break
    }
    $searchRoot = $parent
}

if (-not $pythonPath) {
    throw 'Không tìm thấy .venv\Scripts\python.exe từ thư mục tool trở lên.'
}

Set-Location -LiteralPath $runtimeRoot
& $pythonPath -m uvicorn ai_import.api:app --host 127.0.0.1 --port 8010

