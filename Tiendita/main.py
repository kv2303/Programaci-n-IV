import time
import asyncio
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List

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



inventario = [
    {"id": 1, "nombre": "Casa de campaña", "precio": 750, "cantidad": 10},
    {"id": 2, "nombre": "Botas", "precio": 1200, "cantidad": 5},
    {"id": 3, "nombre": "Linterna de cabeza", "precio": 350, "cantidad": 15},
    {"id": 4, "nombre": "Sleeping", "precio": 900, "cantidad": 10},
    {"id": 5, "nombre": "Linterna de cabeza", "precio": 350, "cantidad": 15}
]

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
    return inventario


@app.get("/productos/{id}")
async def getProductoEspecifico(id: int):
    for p in inventario:
        if p["id"] == id:
            return p
    raise HTTPException(status_code=404, detail="Producto no encontrado")

# Venta relámpago

@app.post("/productos/{producto_id}")
async def comprar_producto(producto_id: int):
    try:
        async with lock: # Punto de control del experimento (comentar para el Exp A)
            for objeto in inventario:
                if objeto["id"] == producto_id:
                    if objeto["cantidad"] > 0:
                        await asyncio.sleep(0.05) # Latencia simulada
                        objeto["cantidad"] -= 1
                        return {"mensaje": "Producto comprado exitosamente"}
                    else:
                        raise HTTPException(400, "No hay stock")
            raise HTTPException(400, "Producto no existe")
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(500, f"Error interno: {str(error)}")

#agregar producto

@app.post("/productos/", response_model=respuestaProducto, status_code=status.HTTP_201_CREATED)
def addProducto(producto: crearProducto):

    try:

        nuevo_id = max((p["id"] for p in inventario), default=0) + 1
        nuevo_producto = {
            "id": nuevo_id,    
            "nombre": producto.nombre,
            "precio": producto.precio,
            "cantidad": producto.cantidad
        }

        inventario.append(nuevo_producto)

        return nuevo_producto
    
    except Exception as error:
        raise HTTPEXception(status_code=500, detail=f"Ocurrio un error al agregar el prodycto: {str(error)}")

#Eliminar producto
@app.delete("/productos/{producto_id}")
def deleteProducto(producto_id: int):
    try: 
        for producto in inventario:
            if producto["id"] == producto_id:
                inventario.remove(producto)
                return {"Message": "El producto fue eliminado"}
        raise HTTPException(status_code=404, detail="No fue encontrado el producto")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
