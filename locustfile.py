from locust import HttpUser, task, between

class PrepForgeUser(HttpUser):
    wait_time = between(1,2)

    @task
    def open_app(self):
        self.client.get("/")
