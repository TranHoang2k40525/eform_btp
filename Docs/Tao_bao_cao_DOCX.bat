@echo off
setlocal
cd /d "%~dp0"
echo Dang tao cac bao cao DOCX thuc tap Tuan 8, 9, 10 va Tong hop...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Tao_bao_cao_DOCX.ps1"
if errorlevel 1 (
  echo.
  echo Khong the tao DOCX. Hay kiem tra moi truong Python hoac cac thu vien can thiet.
  pause
  exit /b 1
)
echo.
echo Da tao xong toan bo cac file DOCX trong thu muc Docs.
pause
