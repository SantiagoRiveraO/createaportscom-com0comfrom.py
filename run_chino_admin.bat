@echo off
echo ========================================
echo    CHINO - GESTOR DE PUERTOS COM
echo    (Ejecutando como Administrador)
echo ========================================
echo.
echo Iniciando aplicación principal como administrador...
echo.

cd /d "C:\Users\santi\Desktop\CHINO"

powershell -Command "Start-Process python -ArgumentList 'main_app.py' -Verb RunAs"

echo.
echo ========================================
echo Aplicación iniciada como administrador.
echo ========================================
echo.
pause 