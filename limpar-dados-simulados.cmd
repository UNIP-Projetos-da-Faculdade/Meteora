@echo off
setlocal
cd /d "%~dp0"
call simular-dados.cmd --limpar
exit /b %errorlevel%
