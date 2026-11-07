@echo off
setlocal
cd /d "%~dp0frontend"
if not exist "node_modules\next\package.json" goto preparar
if not exist ".env.local" goto preparar
echo Painel: http://localhost:3000
echo Mantenha esta janela aberta. Para encerrar, pressione Ctrl+C.
call npm.cmd run dev -- --hostname 0.0.0.0 --port 3000
if errorlevel 1 goto erro
exit /b 0
:preparar
echo Execute preparar.cmd na raiz do projeto primeiro.
:erro
echo Nao foi possivel iniciar o frontend. Confira a mensagem acima.
pause
exit /b 1
