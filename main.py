import torch
import torch.distributed as dist
import torch.multiprocessing as mp
import time
import os

# Matrix sizes (you can adjust this as needed)
matrix_size = 7000
cpu_failed = matrix_size * 10
gpu_out_of_memory = matrix_size * 10

# Generate random matrices
A = torch.randn(matrix_size, matrix_size)
B = torch.randn(matrix_size, matrix_size)

def benchmark(device, use_multiple_gpus=False):
    if use_multiple_gpus:
        # Parallelize over multiple GPUs
        A_split = torch.chunk(A.to(device), torch.cuda.device_count())
        B_split = torch.chunk(B.to(device), torch.cuda.device_count())
    else:
        A_device = A.to(device)
        B_device = B.to(device)

    # Start the timer
    start_time = time.time()

    if use_multiple_gpus:
        # For multiple GPUs: Perform operations on each chunk
        results = [torch.mm(a, b) for a, b in zip(A_split, B_split)]
        C = torch.cat(results).to("cpu")
    else:
        # For single device (CPU or single GPU)
        C = torch.mm(A_device, B_device)
        C.to("cpu")  # Move the result back to CPU

    # End timer
    end_time = time.time()
    return end_time - start_time

# 1. CPU Benchmark
cpu_time = benchmark("cpu")
print(f"Time on CPU: {cpu_time:.3f} seconds")

# 2. Single GPU Benchmark (if available)
if torch.cuda.is_available():
    gpu_time = benchmark("cuda:0")
    print(f"Time on single GPU: {gpu_time:.3f} seconds")

    # 3. Multi-GPU Benchmark (if more than 1 GPU is available)
    if torch.cuda.device_count() > 1:
        multi_gpu_time = benchmark("cuda", use_multiple_gpus=True)
        print(f"Time on multiple GPUs: {multi_gpu_time:.3f} seconds")
else:
    print("No GPU available.")

