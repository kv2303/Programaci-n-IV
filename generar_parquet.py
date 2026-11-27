import numpy as np
import polars as pl
import pandas as pd
from datetime import datetime, timedelta

NUM_REGISTROS = 1_500_000

print(f"Generando {NUM_REGISTROS:,} registros de ventas...")

# 1. Leer productos reales de tu tienda
df_prod = pd.read_csv("productos.csv", encoding="latin1")
nombres = df_prod["nombre"].tolist()
precios = df_prod["precio"].astype(float).tolist()

# 2. Generar índices aleatorios con NumPy
rng = np.random.default_rng(42)
indices = rng.integers(0, len(nombres), size=NUM_REGISTROS)

# 3. Generar fechas aleatorias en los últimos 30 días
fecha_base = datetime.now() - timedelta(days=30)
segundos_aleatorios = rng.integers(0, 30 * 24 * 3600, size=NUM_REGISTROS)
fechas = [
    (fecha_base + timedelta(seconds=int(s))).strftime("%Y-%m-%d %H:%M:%S")
    for s in segundos_aleatorios
]

# 4. Construir columnas con tipos de datos consistentes
ids_venta = np.arange(1, NUM_REGISTROS + 1, dtype=np.int64)
productos_col = [nombres[i] for i in indices]
precios_col = np.array([precios[i] for i in indices], dtype=np.float64)
cantidades_col = rng.integers(1, 5, size=NUM_REGISTROS, dtype=np.int64)
montos_col = np.round(precios_col * cantidades_col, 2)

# 5. Crear DataFrame en Polars y exportar a Parquet
df_ventas = pl.DataFrame({
    "id_venta": ids_venta,
    "fecha": fechas,
    "producto": productos_col,
    "precio": precios_col,
    "cantidad": cantidades_col,
    "monto_total": montos_col,
})

df_ventas.write_parquet("ventas.parquet")
print("Archivo 'ventas.parquet' generado exitosamente.")