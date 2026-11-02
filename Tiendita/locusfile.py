from locust import HttpUser, task, between

class UsuarioTienditaCompleto(HttpUser):
    wait_time = between(0.2, 0.8)

    @task(3)
    def comprarProducto(self):
        # catch_response evita registrar 400 como falla
        with self.client.post("/productos/3", catch_response=True) as response:
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