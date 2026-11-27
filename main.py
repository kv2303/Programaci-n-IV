import time
import asyncio
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pydantic import BaseModel, Field
from typing import List
import pandas as pd
import csv
from datetime import datetime
import os
from contextlib import asynccontextmanager
import polars as pl


# ELIMINAR la lista 'inventario = [...]'
# Asegurar que existan los archivos base
lock = asyncio.Lock()

COLUMNAS_VENTAS = ["id_venta", "fecha", "producto", "precio", "cantidad", "monto_total"]

if not os.path.exists("productos.csv"):
    pd.DataFrame(columns=["id", "nombre", "precio", "cantidad"]).to_csv("productos.csv", index=False)
if not os.path.exists("ventas.csv"):
    pd.DataFrame(columns=COLUMNAS_VENTAS).to_csv("ventas.csv", index=False)

SCHEMA_VENTAS = {
    "id_venta": pl.Int64,
    "fecha": pl.Utf8,
    "producto": pl.Utf8,
    "precio": pl.Float64,
    "cantidad": pl.Int64,
    "monto_total": pl.Float64,
}

async def corte_de_caja():
    async with lock:
        if not os.path.exists("ventas.csv"):
            return
        try:
            df_csv = pl.read_csv("ventas.csv", schema=SCHEMA_VENTAS, encoding="utf8-lossy")
            if df_csv.is_empty():
                print("[Corte de Caja] Sin ventas nuevas en turno.")
                return

            if os.path.exists("ventas.parquet"):
                df_parquet = pl.read_parquet("ventas.parquet")
                df_final = pl.concat([df_parquet, df_csv])
            else:
                df_final = df_csv

            # Guardar Parquet actualizado y vaciar CSV dejando solo encabezados
            df_final.write_parquet("ventas.parquet")
            with open("ventas.csv", "w", encoding="utf-8") as f:
                f.write(",".join(COLUMNAS_VENTAS) + "\n")

            print(f"[Corte de Caja] {df_csv.height} ventas archivadas en ventas.parquet.")
        except Exception as e:
            print(f"[Corte de Caja] Error: {e}")

# --- CICLO DE VIDA (LIFESPAN) DE FASTAPI ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = AsyncIOScheduler()
    # Configurado cada 2 minutos para demostración en clase
    scheduler.add_job(corte_de_caja, "interval", minutes=2)
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(title="API Proyecto Tiendita", lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


'''inventario = [
    {"id": 1, "nombre": "Casa de campaña", "precio": 750, "cantidad": 10},
    {"id": 2, "nombre": "Botas", "precio": 1200, "cantidad": 5},
    {"id": 3, "nombre": "Linterna de cabeza", "precio": 350, "cantidad": 15},
    {"id": 4, "nombre": "Sleeping", "precio": 900, "cantidad": 10},
    {"id": 5, "nombre": "Linterna de cabeza", "precio": 350, "cantidad": 15}
]'''

#Modelos de pydantic para validar los datos de entrada y salida de la API
class crearProducto(BaseModel):
    nombre: str = Field(..., min_length=1, description="Nombre del producto")
    precio: float = Field(..., gt=0, description="Precio del producto")
    cantidad: int = Field(..., ge=0, description="Cantidad del producto")
#Modelo pydantic para la respuesta de los productos
class respuestaProducto(BaseModel):
    id: int
    nombre: str
    precio: float
    cantidad: int


@app.get("/")
def home():
    return {"Message": "Hola bienvenido"}
@app.get("/productos")

def getProductos():
    df = pd.read_csv("productos.csv", encoding= "latin1")
    return df.to_dict(orient="records")

#Obtener producto

@app.get("/productos/{id}")
async def getProductoEspecifico(id: int):
    for p in df:
        if p["id"] == id:
            return p
    raise HTTPException(status_code=404, detail="Producto no encontrado")


# Agregar producto

@app.post("/productos", response_model=respuestaProducto, status_code=status.HTTP_201_CREATED)
async def addProducto(producto: crearProducto):
    async with lock:
        df = pd.read_csv("productos.csv", encoding="latin1")
        nombre_limpio = producto.nombre.strip().lower()

        # Buscar si ya existe un producto con el mismo nombre
        coincidencia = df[df["nombre"].astype(str).str.strip().str.lower() == nombre_limpio]

        if not coincidencia.empty:
            idx = coincidencia.index[0]
            df.at[idx, "cantidad"] = int(df.at[idx, "cantidad"]) + producto.cantidad
            df.at[idx, "precio"] = producto.precio
            df.to_csv("productos.csv", index=False, encoding="latin1")

            return {
                "id": int(df.at[idx, "id"]),
                "nombre": str(df.at[idx, "nombre"]),
                "precio": float(df.at[idx, "precio"]),
                "cantidad": int(df.at[idx, "cantidad"]),
            }

        # Si no existe, se crea uno nuevo
        nuevo_id = int(df["id"].max() + 1) if not df.empty else 1
        nuevo_producto = {
            "id": nuevo_id,
            "nombre": producto.nombre.strip(),
            "precio": producto.precio,
            "cantidad": producto.cantidad,
        }

        df.loc[len(df)] = nuevo_producto
        df.to_csv("productos.csv", index=False, encoding="latin1")
        return nuevo_producto

#Eliminar producto

@app.delete("/productos/{producto_id}")
def deleteProducto(producto_id: int):
    df = pd.read_csv("productos.csv", encoding="latin1")
    if producto_id not in df["id"].values:
        raise HTTPException(status_code=404, detail="No fue encontrado el producto")
    df = df[df["id"] != producto_id]
    df.to_csv("productos.csv", index=False, encoding="latin1")
    return {"Message": "El producto fue eliminado"}

@app.post("/productos/{producto_id}")
async def comprar_producto(producto_id: int, cantidad: int= 1):
    try:
        if cantidad <= 0:
            raise HTTPException(400, "La cantidad debe ser mayor a 0")
        
        async with lock:
            df_prod = pd.read_csv("productos.csv", encoding="latin1")
            
            if producto_id not in df_prod["id"].values:
                raise HTTPException(400, "Producto no existe")
                
            idx = df_prod.index[df_prod["id"] == producto_id].tolist()[0]
            stock_actual = int(df_prod.at[idx, "cantidad"])

            if stock_actual >= cantidad:
                df_prod.at[idx, "cantidad"] = stock_actual - cantidad
                df_prod.to_csv("productos.csv", index=False, encoding="latin1")
                
                precio_unit = float(df_prod.at[idx, "precio"])
                
                nueva_venta = {
                    "id_venta": int(time.time() * 1000),
                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "producto": str(df_prod.at[idx, "nombre"]),
                    "precio": precio_unit,
                    "cantidad": cantidad,
                    "monto_total": round(precio_unit * cantidad, 2)
                }
                # Guardamos la venta
                existe = os.path.exists("ventas.csv") and os.path.getsize("ventas.csv") > 0 
                pd.DataFrame([nueva_venta]).to_csv(
                    "ventas.csv", mode='a', header=not existe, index=False, encoding="utf-8"
                )

                
                return {"mensaje": f"Tu producto se compró exitosamente: {cantidad} unidad(es)"}
            else:
                raise HTTPException(400, f"Stock insuficiente (disponible: {stock_actual})")
    except HTTPException:
        raise
    except Exception as error:
        # Esto atrapará cualquier error de Python y lo enviará al navegador
        raise HTTPException(500, f"Error interno: {str(error)}")

@app.get("/api/analisis/kpis")
def obtener_kpis():
    try:
            lf = obtener_ventas_combinadas()
            resumen = lf.select([
                pl.col("monto_total").sum().alias("ingresos_totales"),
                pl.len().alias("total_transacciones"),
            ]).collect()

            estrella = (
                lf.group_by("producto")
                .agg(pl.col("cantidad").sum().alias("total_vendido"))
                .sort("total_vendido", descending=True)
                .limit(1)
                .collect()
            )

            return {
                "ingresos_totales": round(resumen["ingresos_totales"][0] or 0.0, 2),
                "total_transacciones": int(resumen["total_transacciones"][0] or 0),
                "producto_estrella": estrella["producto"][0] if not estrella.is_empty() else "N/A",
            }
    except Exception as e:
            return {"error": str(e)}


@app.get("/api/analisis/mas-vendidos")
def obtener_datos_graficas():
    try:
            lf = obtener_ventas_combinadas()

            por_producto = (
                lf.group_by("producto")
                .agg(pl.col("monto_total").sum().alias("ingresos"))
                .sort("ingresos", descending=True)
                .collect()
                .to_dicts()
            )

            por_fecha = (
                lf.with_columns(pl.col("fecha").str.slice(0, 10).alias("fecha_corta"))
                .group_by("fecha_corta")
                .agg(pl.col("monto_total").sum().alias("ingresos"))
                .sort("fecha_corta")
                .collect()
                .to_dicts()
            )

            return {
                "ventas_por_producto": {r["producto"]: round(r["ingresos"], 2) for r in por_producto},
                "ventas_por_fecha": {r["fecha_corta"]: round(r["ingresos"], 2) for r in por_fecha},
            }
    except Exception as e:
            return {"error": str(e)}

def obtener_ventas_combinadas() -> pl.LazyFrame:
    frames = []
    if os.path.exists("ventas.parquet"):
        frames.append(pl.scan_parquet("ventas.parquet"))
    if os.path.exists("ventas.csv") and os.path.getsize("ventas.csv") > 0:
        frames.append(pl.scan_csv("ventas.csv", schema=SCHEMA_VENTAS, encoding="utf8-lossy"))
    
    if not frames:
        return pl.DataFrame(schema=SCHEMA_VENTAS).lazy()
    return pl.concat(frames)