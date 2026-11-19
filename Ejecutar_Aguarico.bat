@echo off
title Sistema Agrupacion Aguarico v6
cd /d "%~dp0"
python main_aguarico_v6_login_asistencia.py
if errorlevel 1 (
    echo.
    echo Ocurrio un error al ejecutar la aplicacion.
    pause
)
