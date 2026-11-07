@echo off
setlocal
cd /d "%~dp0backend"
if not exist ".venv\Scripts\python.exe" goto preparar
if not exist ".env" goto preparar
".venv\Scripts\python.exe" -u -m scripts.simular_esp32 %*
if errorlevel 1 goto erro
exit /b 0
:preparar
echo Execute preparar.cmd na raiz do projeto primeiro.
:erro
echo Nao foi possivel executar a simulacao. Confira a mensagem acima.
pause
exit /b 1
