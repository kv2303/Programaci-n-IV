@echo off
echo Iniciando el servidor de la tienda...
start cmd /k "uvicorn main:app"
timeout /t 3 /nobreak > NUL
start http://127.0.0.1:8000/index.html
