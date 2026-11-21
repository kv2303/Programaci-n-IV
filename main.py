import time
import asyncio
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List
import pandas as pd
import csv
from datetime import datetime
import os

# ELIMINAR la lista 'inventario = [...]'
# Asegurar que existan los archivos base
if not os.path.exists("productos.csv"):
    pd.DataFrame(columns=["id", "nombre", "precio", "cantidad"]).to_csv("productos.csv", index=False)
if not os.path.exists("ventas.csv"):
    pd.DataFrame(columns=["fecha", "producto_id", "precio", "cantidad", "monto_total"]).to_csv("ventas.csv", index=False)


app = FastAPI(title="API Proyecto Tiendita")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Cerrojo para sincronización asíncrona 
lock = asyncio.Lock()



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
def addProducto(producto: crearProducto):
    df = pd.read_csv("productos.csv", encoding="latin1")
    nuevo_id = int(df["id"].max() + 1) if not df.empty else 1
    nuevo_producto = {
        "id": nuevo_id, 
        "nombre": producto.nombre, 
        "precio": producto.precio, 
        "cantidad": producto.cantidad
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
async def comprar_producto(producto_id: int):
    try:
        async with lock:
            df_prod = pd.read_csv("productos.csv", encoding="latin1")
            
            if producto_id not in df_prod["id"].values:
                raise HTTPException(400, "Producto no existe")
                
            idx = df_prod.index[df_prod["id"] == producto_id].tolist()[0]
            if df_prod.at[idx, "cantidad"] > 0:
                df_prod.at[idx, "cantidad"] -= 1
                df_prod.to_csv("productos.csv", index=False, encoding="latin1")
                
                # Registrar en ventas.csv
                nueva_venta = {
                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "producto_id": producto_id,
                    "precio": df_prod.at[idx, "precio"],
                    "cantidad": 1,
                    "monto_total": df_prod.at[idx, "precio"]
                }
                # Guardamos la venta
                pd.DataFrame([nueva_venta]).to_csv("ventas.csv", mode='a', header=not os.path.exists("ventas.csv"), index=False, encoding="latin1")
                
                return {"mensaje": "Producto comprado exitosamente"}
            else:
                raise HTTPException(400, "No hay stock")
    except HTTPException:
        raise
    except Exception as error:
        # Esto atrapará cualquier error de Python y lo enviará al navegador
        raise HTTPException(500, f"Error interno: {str(error)}")

@app.get("/api/kpis")
def obtener_kpis():
    try:
        df_ventas = pd.read_csv("ventas.csv", encoding="latin1")
        if df_ventas.empty: return {"ingresos_totales": 0, "total_transacciones": 0, "producto_estrella": "N/A"}
        
        ingresos = df_ventas["monto_total"].sum()
        transacciones = len(df_ventas)
        prod_estrella = df_ventas["producto_id"].value_counts().idxmax()
        
        return {
            "ingresos_totales": float(ingresos),
            "total_transacciones": int(transacciones),
            "producto_estrella": int(prod_estrella)
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/graficas")
def obtener_datos_graficas():
    try:
        df_ventas = pd.read_csv("ventas.csv", encoding="latin1")
        
        # Si el archivo está vacío (no hay ventas aún)
        if df_ventas.empty: 
            return {"ventas_por_producto": {}, "ventas_por_fecha": {}}
        
        # 1. Agrupar por producto
        agrupado_prod = df_ventas.groupby("producto_id")["monto_total"].sum().to_dict()
        
        # 2. Agrupar por fecha
        df_ventas['fecha_corta'] = pd.to_datetime(df_ventas['fecha']).dt.date.astype(str)
        agrupado_fecha = df_ventas.groupby("fecha_corta")["monto_total"].sum().to_dict()

        # AQUÍ ESTÁ LA CLAVE: Se envían ambos diccionarios
        return {
            "ventas_por_producto": agrupado_prod,
            "ventas_por_fecha": agrupado_fecha
        }
    except Exception as e:
        # Si hay un error, lo enviamos para saber qué pasó
        return {"error": str(e)}