@echo off
if not exist ventas.parquet (
    echo Generando base historica de 1.5 millones de ventas...
    python generar_parquet.py
)
echo Iniciando el servidor de la tienda...
start cmd /k "python -m uvicorn main:app"
timeout /t 3 /nobreak > NUL
start index.html