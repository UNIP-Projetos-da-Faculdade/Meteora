@echo off
setlocal
cd /d "%~dp0..\backend"
if not exist ".venv\Scripts\python.exe" goto preparar
if not exist ".env" goto preparar
".venv\Scripts\python.exe" -u -m scripts.validar_integracao %*
if errorlevel 1 goto erro
echo.
echo Validacao de software concluida. O teste fisico do ESP32 continua necessario.
if not defined METEORA_SEM_PAUSA pause
exit /b 0
:preparar
echo Execute scripts\preparar.cmd primeiro.
:erro
echo A validacao falhou. Confira a mensagem acima e o README.md da raiz.
if not defined METEORA_SEM_PAUSA pause
exit /b 1
