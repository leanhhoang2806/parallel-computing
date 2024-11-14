import socket
import pickle
import time
from models import SchedulerInfo, WorkerInfo

class Worker:
    def __init__(self, host: str, port: int, schedulerInfo: SchedulerInfo) -> None:
        self.host = host
        self.port = port
        self.schedulerInfo = schedulerInfo

    def connect_to_scheduler(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.schedulerInfo.host, self.schedulerInfo.port))
            worker_info = WorkerInfo(host=self.host, port=self.port)
            serialized_info = pickle.dumps(worker_info)
            s.sendall(serialized_info)
            print(f"Registered with scheduler at {self.schedulerInfo.host}:{self.schedulerInfo.port}")
    
    def listen_for_tasks(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen(5)
            print(f"Worker listening for tasks on {self.host}:{self.port}")
            while True:
                conn, addr = s.accept()
                with conn:
                    print(f"Received connection from scheduler at {addr}")
                    task = pickle.loads(conn.recv(4096))
                    print(f"Received task: {task}")
                    self.process_task(task)
                    time.sleep(1)  # Simulate task processing

    def process_task(self, task):
        """Process the received task."""
        print(f"Processing task: {task}")
        # Here we would add actual processing logic
        # For now, just simulate some processing time
        time.sleep(2)
        print("Task completed")

if __name__ == "__main__":
    # Replace these with the worker's IP and port and scheduler's IP and port
    worker_host = "0.0.0.0"  # Worker IP address
    worker_port = 65433       # Worker port (unique for each worker)
    scheduler_host = "192.168.1.15"  # Scheduler IP address
    scheduler_port = 65432            # Scheduler port

    worker = Worker(worker_host, worker_port, SchedulerInfo(scheduler_host, scheduler_port))
    worker.connect_to_scheduler()
    worker.listen_for_tasks()