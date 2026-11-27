from locust import HttpUser, task, between

class UsuarioTienditaCompleto(HttpUser):
    wait_time = between(0.2, 0.8)

    @task(3)

    def comprarProducto(self):
        # Cambia el "3" por un ID que sepas que existe en tu archivo CSV personalizado.
        with self.client.post("/productos/1", catch_response=True) as response: 
            if response.status_code in [200, 400]:
                response.success()
            else:
                response.failure(f"Error inesperado: {response.status_code}")

    @task(1)
    def getProducto(self):
        self.client.get("/")

    @task(2)
    def consultarCatalogo(self):
        self.client.get("/productos")