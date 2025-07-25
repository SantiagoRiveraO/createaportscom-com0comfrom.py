@echo off
echo ========================================
echo    PRUEBA AUTOMATICA DE PUERTOS COM
echo ========================================
echo.
echo Ejecutando como administrador...
echo.

cd /d "C:\Users\santi\Desktop\CHINO"

echo Iniciando prueba del sistema automatico...
python test_auto_ports.py

echo.
echo ========================================
echo Prueba completada. Revisa los resultados arriba.
echo ========================================
echo.
pause 