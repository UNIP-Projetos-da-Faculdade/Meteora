@echo off
setlocal
cd /d "%~dp0backend"
if not exist ".venv\Scripts\python.exe" goto preparar
if not exist ".env" goto preparar
".venv\Scripts\python.exe" -m scripts.verificar_ambiente
if errorlevel 1 goto erro
echo.
echo API: http://localhost:8000/docs
echo Mantenha esta janela aberta. Para encerrar, pressione Ctrl+C.
".venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000
if errorlevel 1 goto erro
exit /b 0
:preparar
echo Execute preparar.cmd na raiz do projeto primeiro.
:erro
echo Nao foi possivel iniciar o backend. Confira a mensagem acima.
pause
exit /b 1
