@echo off
echo ========================================
echo   Discord Bot - Iniciar Servicios
echo ========================================
echo.

REM Activar entorno virtual
call venv\Scripts\activate.bat

echo [1/2] Iniciando Bot de Discord...
start "Discord Bot" cmd /k "venv\Scripts\activate.bat && python -m bot.main"

timeout /t 3 /nobreak >nul

echo [2/2] Iniciando Panel Web...
start "Panel Web" cmd /k "venv\Scripts\activate.bat && python -m web.main"

echo.
echo ========================================
echo   Servicios iniciados correctamente
echo ========================================
echo.
echo Bot de Discord: Terminal 1
echo Panel Web: http://localhost:8000
echo.
echo Presiona cualquier tecla para cerrar esta ventana...
pause >nul
