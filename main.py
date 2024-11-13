import torch
import torch.distributed as dist
import torch.multiprocessing as mp
import time
import os

# Matrix sizes (you can adjust this as needed)
matrix_size = 5000*2

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

# 4. Distributed Training Benchmark
def init_process(rank, world_size, backend="nccl"):
    os.environ['MASTER_ADDR'] = '127.0.0.1'
    os.environ['MASTER_PORT'] = '29500'
    dist.init_process_group(backend, rank=rank, world_size=world_size)

    # Move A and B to the specific GPU for this rank
    device = torch.device(f"cuda:{rank}")
    A_device = A.to(device)
    B_device = B.to(device)

    # Start timer
    start_time = time.time()
    
    # Perform matrix multiplication in parallel
    C = torch.mm(A_device, B_device)
    
    # Synchronize all processes
    dist.barrier()
    
    # End timer
    end_time = time.time()
    if rank == 0:
        print(f"Time on distributed setup with {world_size} GPUs: {end_time - start_time:.3f} seconds")

    dist.destroy_process_group()

if torch.cuda.device_count() > 1:
    world_size = torch.cuda.device_count()
    mp.spawn(init_process, args=(world_size,), nprocs=world_size)
