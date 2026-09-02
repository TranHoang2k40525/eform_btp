$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$main = Join-Path (Split-Path -Parent $root) 'Main'
$env:PYTHONPATH = $main
& (Join-Path $main '.venv\Scripts\python.exe') -m pytest $root -q --cov=ai_import --cov-report=term-missing

