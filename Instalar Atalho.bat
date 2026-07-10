@echo off
REM Cria um atalho "Jornada" na Area de Trabalho apontando para este repositorio.
REM Rode uma vez em cada PC (duplo-clique).
setlocal
set "REPO=%~dp0"
if "%REPO:~-1%"=="\" set "REPO=%REPO:~0,-1%"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ws = New-Object -ComObject WScript.Shell;" ^
  "$lnk = $ws.CreateShortcut([IO.Path]::Combine([Environment]::GetFolderPath('Desktop'),'Jornada.lnk'));" ^
  "$lnk.TargetPath = 'C:\Windows\System32\wscript.exe';" ^
  "$lnk.Arguments = '\"%REPO%\Jornada.vbs\"';" ^
  "$lnk.WorkingDirectory = '%REPO%';" ^
  "$lnk.IconLocation = '%REPO%\app\static\jornada.ico,0';" ^
  "$lnk.Description = 'Abre o Jornada como aplicativo';" ^
  "$lnk.Save();" ^
  "Write-Host 'Atalho Jornada criado na Area de Trabalho.'"

echo.
pause
