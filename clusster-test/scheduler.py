import socket
import threading
import pickle
import queue
import time
from models import InternalParameters, WorkerInfo, Task
from fastapi import FastAPI
from typing import Any
import uvicorn


class Scheduler:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.tasks_queue = queue.Queue()
        self.ready_workers = queue.Queue()
        self.busy_workers = {}

        self.internal_parameters = InternalParameters(
            wait_time=5
        )
        self.app = FastAPI()
        self._setup_routes()

    def _setup_routes(self):
        @self.app.post("/add_task/")
        async def add_task(task: Task):
            """Endpoint to add a new task to the queue."""
            self.tasks_queue.put(task)
            return {"message": "Task added successfully", "task": task}

    def run_https_server(self):
        """Run HTTPS server with FastAPI on a separate thread."""
        # Replace "cert.pem" and "key.pem" with your actual certificate and key files
        uvicorn.run(self.app)

    def add_task(self, task):
        self.tasks_queue.put(task)
    
    def register_worker(self, worker_socket: WorkerInfo):
        self.ready_workers.put(worker_socket)

    def _sleep_if_worker_not_available(self) -> bool:
        if self.ready_workers.empty():
            print("No worker available at the moment")
            time.sleep(self.internal_parameters.wait_time)
            return True
        return False
    
    def _sleep_if_no_task_to_process(self) -> bool:
        if self.tasks_queue.empty(): 
            print("No task available at the moment")
            time.sleep(self.internal_parameters.wait_time)
            return True
        return False

    def _send_task(self, worker: WorkerInfo, task: Task):
        """Open a Connection to worker and send task over"""
        serialized_task = pickle.dumps(task)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((worker.host, worker.port))
            s.sendall(serialized_task)

            print(f"Task sent to worker at {worker.host}:{worker.port}")

    def _worker_connection_skip(self, server_socket):
        try:
            connection, address = server_socket.accept()
            print(f"Connected to worker at {address}")
            data = connection.recv(1024)  # Adjust buffer size as needed
            worker_info = pickle.loads(data)
            print(f"Received worker info: {worker_info.host}:{worker_info.port}")

            # Add deserialized worker info to the ready_workers queue
            self.ready_workers.put(worker_info)
            print(f"Worker registered: {worker_info.host}:{worker_info.port}")
        except BlockingIOError:
            pass

    def run(self):
        print("Running the Scheduler")
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        print("Scheduler is running and ready for connections.")
        while True:
            self._worker_connection_skip(server_socket)
            current_worker = self.ready_workers.get()
            print(f"current worker = {current_worker}")
            current_task = self.tasks_queue.get()
            self._send_task(current_worker, current_task)
            time.sleep(10)

if __name__ == "__main__":
    scheduler = Scheduler("0.0.0.0", 65432)

    threading.Thread(target=scheduler.run_https_server, daemon=True).start()
    scheduler.run()
            
