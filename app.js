const API_URL = "http://127.0.0.1:8000/productos";

// Selección de Elementos del DOM
const formProducto = document.getElementById("formProducto");
const tablaProductos = document.getElementById("tablaProductos");
const totalProductos = document.getElementById("totalProductos");
let miGrafica = null; // Variable para almacenar la instancia de la gráfica y destruirla luego
let miGraficaLineas = null;
// 1. Función para Cargar Productos (GET)
async function cargarProductos() {
    try {
        const respuesta = await fetch(API_URL);
        const productos = await respuesta.json();

        tablaProductos.innerHTML = "";
        totalProductos.textContent = `${productos.length} productos`;

        if (productos.length === 0) {
            tablaProductos.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center text-muted py-4">
                        No hay productos registrados en la tiendita.
                    </td>
                </tr>`;
            return;
        }

        

        productos.forEach(p => {
            const fila = document.createElement("tr");
            fila.innerHTML = `
                <td class="fw-bold text-secondary">#${p.id}</td>
                <td>${p.nombre}</td>
                <td class="text-success fw-bold">$${p.precio}</td>
                <td>
                    <span class="badge ${p.cantidad < 10 ? 'bg-danger' : 'bg-success'}">
                        ${p.cantidad} unidades
                    </span>
                </td>
                <td class="text-end">
                    
                    <button class="btn btn-outline-primary btn-sm me-2" onclick="comprarRelampago(${p.id})">
                        <i class="bi bi-cart"></i> Comprar
                    </button>

                    <button class="btn btn-outline-danger btn-sm" onclick="eliminarProducto(${p.id})">
                        <i class="bi bi-trash"></i> Eliminar
                    </button>
                </td>
            `;
            tablaProductos.appendChild(fila);
        });

    } catch (error) {
        console.error("Error al cargar productos:", error);
    }
}

async function agregarProducto(event){
    event.preventDefault();

    var nombre = document.getElementById("nombre").value
    var precio = document.getElementById("precio").value
    var cantidad = document.getElementById("cantidad").value

    const nuevoContenido = {nombre, precio, cantidad}
    try {
        const respuesta = await fetch(API_URL, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(nuevoContenido)});

        if(respuesta){
            formProducto.reset();
            await cargarProductos();
        }else{
            console.error("Hubo algo malo al guardar")
        }
    } catch (error) {
        console.log(error)
    }
}

async function eliminarProducto(id_producto){
    event.preventDefault();

    try {
        const respuesta = await fetch("http://127.0.0.1:8000/productos/"+id_producto, {method: "DELETE", headers: {"Content-Type": "application/json"}});

        if(respuesta){
            await cargarProductos();
        }else{
            console.error("Hubo algo malo al eliminar")
        }
    } catch (error) {
        console.log(error)
    }
}



// Cargar catálogo al abrir la página
document.addEventListener("DOMContentLoaded", async () => {
    await cargarProductos();
    await cargarDashboard();
});

// Agregamos el evento para que se abre la función al dar clic en guardar producto
formProducto.addEventListener("submit", agregarProducto);


formProducto.addEventListener("submit", agregarProducto);

// Función para simular la compra desde la interfaz
async function comprarRelampago(id_producto) {
    try {
        const respuesta = await fetch(`${API_URL}/${id_producto}`, { 
            method: "POST",
            headers: {"Content-Type": "application/json"}
        });
        
        const data = await respuesta.json();
        
        if(respuesta.ok) {
            alert("¡Éxito! " + data.mensaje);
        } else {
            alert("Fallo la compra: " + data.detail);
        }
        // Actualizar la tabla después del intento
        await cargarProductos();
        await cargarDashboard();
    } catch (error) {
        console.error("Error en la compra:", error);
        alert("Error de conexión");
    }
}

async function cargarDashboard() {
    // Cargar KPIs
    const resKpi = await fetch("http://127.0.0.1:8000/api/kpis");
    const kpis = await resKpi.json();
    
    // Asumiendo que tienes elementos HTML con estos IDs en tu index.html
    document.getElementById("kpiIngresos").textContent = `$${kpis.ingresos_totales}`;
    document.getElementById("kpiTransacciones").textContent = kpis.total_transacciones;
    document.getElementById("kpiEstrella").textContent = `ID: ${kpis.producto_estrella}`;

    // Cargar Gráfica
    const resGraf = await fetch("http://127.0.0.1:8000/api/graficas");
    const datosGraf = await resGraf.json();
    
    renderizarGrafica(datosGraf.ventas_por_producto, datosGraf.v);
}

// Agregamos "= {}" como valor por defecto por si los datos fallan
function renderizarGrafica(datosBarras = {}, datosLineas = {}) {
    
    // 1. Gráfica de Barras
    const ctx = document.getElementById('miCanvas').getContext('2d');
    if (miGrafica) miGrafica.destroy();
    
    miGrafica = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(datosBarras).map(id => `Prod ${id}`),
            datasets: [{
                label: 'Ingresos por Producto ($)',
                data: Object.values(datosBarras),
                backgroundColor: 'rgba(31, 56, 73, 0.5)'
            }]
        }
    });

    // 2. Gráfica de Líneas
    const ctxLineas = document.getElementById('graficaLineas').getContext('2d');
    if (miGraficaLineas) miGraficaLineas.destroy();
    
    miGraficaLineas = new Chart(ctxLineas, {
        type: 'line',
        data: {
            // Ahora si datosLineas no existe, Object.keys no lanzará error
            labels: Object.keys(datosLineas), 
            datasets: [{
                label: 'Tendencia de Ingresos ($)',
                data: Object.values(datosLineas),
                borderColor: 'rgba(255, 99, 132, 1)',
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                borderWidth: 2,
                fill: true,
                tension: 0.3
            }]
        }
    });
}

