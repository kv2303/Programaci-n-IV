# Tiendita de camping — Proyecto Integrador Final (Programación IV)

Sistema web para la gestión de inventario, ventas en tiempo real y análisis de Big Data sobre millones de transacciones históricas sin detener la operación continua de la tienda.

---

## Resumen de Implementación por Unidad

| Unidad | Enfoque Técnico | Funcionalidad Implementada |
| :--- | :--- | :--- |
| **Unidad 1** | Arquitectura API y Cliente Web | Servidor REST con **FastAPI** y cliente web en **HTML, Bootstrap y JavaScript** consumiendo la API mediante peticiones asíncronas (`fetch()`). |
| **Unidad 2** | Concurrencia y Tolerancia a Fallas | Validación de datos con **Pydantic**, manejo de excepciones HTTP (`400`, `404`, `500`) y protección contra condiciones de carrera mediante `asyncio.Lock()`. |
| **Unidad 3** | Persistencia y Visualización | Inventario persistente en `productos.csv`, registro transaccional en `ventas.csv` y dashboard interactivo con tarjetas KPI y gráficas de barras y líneas en **Chart.js**. |
| **Unidad 4** | Big Data y Operación 24/7 | Generación masiva de 1,500,000 ventas con **NumPy**, almacenamiento columnar en `ventas.parquet`, consultas paralelas con **Polars** (unión virtual en RAM sin duplicados) y corte de caja automático en segundo plano con **APScheduler**. |

---

## Funcionalidades Principales

- **Gestión de Inventario:** Alta, consulta y eliminación de productos. Si se registra un producto con un nombre ya existente, se suman las nuevas unidades al stock actual sin duplicar el ID.
- **Compras en Tiempo Real:** Soporte para comprar una o varias unidades a la vez (con validación de stock) y botón de Venta Relámpago. Cada compra se guarda únicamente en `ventas.csv` bajo `asyncio.Lock()` sin reescribir el archivo histórico.
- **Dashboard Analítico Multi-Núcleo:** Los endpoints `/api/analisis/kpis` y `/api/analisis/mas-vendidos` utilizan `pl.scan_parquet()` y `pl.scan_csv()` concatenados virtualmente en memoria (`pl.concat()`) para reflejar cada compra al instante sobre el total histórico.
- **Corte de Caja Automático 24/7:** Integrado en el `lifespan` de FastAPI mediante `AsyncIOScheduler`. Cada 2 minutos fusiona las ventas nuevas de `ventas.csv` dentro de `ventas.parquet` y limpia `ventas.csv` dejando solo sus encabezados.

---

## Estructura del Proyecto

- `main.py` — Backend en FastAPI, lógica transaccional, endpoints analíticos con Polars y scheduler de corte de caja.
- `generar_parquet.py` — Script generador de 1,500,000 registros de ventas simuladas con NumPy y Polars.
- `productos.csv` — Catálogo e inventario actual de la tienda.
- `ventas.csv` — Buffer transaccional de ventas del turno actual (esquema: `id_venta,fecha,producto,precio,cantidad,monto_total`).
- `index.html` y `app.js` — Interfaz web del catálogo, compras y dashboard con Chart.js.
- `iniciar_tienda.bat` — Lanzador automático para Windows.

---

## Librerías Requeridas

- `fastapi`
- `uvicorn`
- `pandas`
- `polars`
- `numpy`
- `apscheduler`

Instalación rápida:

```bash
pip install fastapi uvicorn pandas polars numpy apscheduler


Para iniciar rápidamente la tienda:

Haz doble clic en iniciar_tienda.bat. El script verificará automáticamente si ventas.parquet existe (si no, ejecutará generar_parquet.py), iniciará el servidor de FastAPI y abrirá index.html en tu navegador.
