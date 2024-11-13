import socket
import threading
import pickle
import queue
import time
from pydantic import BaseModel

class InternalParameters(BaseModel):
    wait_time: int

class WorkerInfo(BaseModel):
    host: str
    port: int

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

    def _send_task(self, worker: WorkerInfo, task):
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
            self.ready_workers.put(connection)
        except BlockingIOError:
            pass

    def run(self):
        print("Running the worker")
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        server_socket.setblocking(False) 
        print("Scheduler is running and ready for connections.")
        while True:
            self._worker_connection_skip(server_socket)
            if not self._sleep_if_worker_not_available(): continue
            if not self._sleep_if_no_task_to_process(): continue
            current_worker = self.ready_workers.get()
            current_task = self.tasks_queue.get()
            self._send_task(current_worker, current_task)

if __name__ == "__main__":
    scheduler = Scheduler("localhost", 65432)
    
            
