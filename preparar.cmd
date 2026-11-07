@echo off
setlocal
cd /d "%~dp0"
echo Preparando o Meteora. Execute este arquivo uma vez em cada computador.
python -c "import sys; sys.exit(0 if sys.version_info >= (3,12) else 1)" >nul 2>&1
if errorlevel 1 (
  echo Instale Python 3.12 ou superior e marque Add python.exe to PATH.
  goto erro
)
node -e "const [a,b]=process.versions.node.split('.').map(Number); process.exit(a>22 || a===22 && b>=18 ? 0 : 1)" >nul 2>&1
if errorlevel 1 (
  echo Instale Node.js 22.18 ou superior.
  goto erro
)
if not exist "backend\.env" copy "backend\.env.example" "backend\.env" >nul
if not exist "frontend\.env.local" copy "frontend\.env.example" "frontend\.env.local" >nul
if not exist "backend\.venv\Scripts\python.exe" python -m venv "backend\.venv"
if errorlevel 1 goto erro
"backend\.venv\Scripts\python.exe" -m pip install -r "backend\requirements-dev.txt"
if errorlevel 1 goto erro
pushd frontend
call npm.cmd ci --no-audit --no-fund
if errorlevel 1 (
  popd
  goto erro
)
popd
echo.
echo Preparacao concluida. Configuracoes locais existentes foram preservadas.
echo 1. Execute iniciar-backend.cmd
echo 2. Execute iniciar-frontend.cmd
echo 3. Execute simular-dados.cmd para testar sem sensores
echo Leia COMECAR-AQUI.md para o passo a passo e a configuracao do ESP32.
pause
exit /b 0
:erro
echo.
echo A preparacao falhou. Confira a mensagem acima e COMECAR-AQUI.md.
pause
exit /b 1
