@echo off
setlocal
cd /d "%~dp0..\backend"
if not exist ".venv\Scripts\python.exe" goto preparar
if not exist ".env" goto preparar
".venv\Scripts\python.exe" -u -m scripts.simular_esp32 %*
if errorlevel 1 goto erro
exit /b 0
:preparar
echo Execute scripts\preparar.cmd primeiro.
:erro
echo Nao foi possivel executar a simulacao. Confira a mensagem acima.
if not defined METEORA_SEM_PAUSA pause
exit /b 1
