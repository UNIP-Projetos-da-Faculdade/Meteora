@echo off
setlocal
cd /d "%~dp0"
call "%~dp0simular-dados.cmd" --limpar
exit /b %errorlevel%
