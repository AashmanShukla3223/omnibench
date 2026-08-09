import os
import sys
import time
import psutil
import numpy as np

print("Testing ONNX Runtime and system memory usage...")
process = psutil.Process(os.getpid())

def get_ram_mb():
    return process.memory_info().rss / (1024 * 1024)

ram_start = get_ram_mb()
print(f"Base process RAM: {ram_start:.2f} MB")

import onnxruntime as ort

ram_after_import = get_ram_mb()
print(f"RAM after onnxruntime import: {ram_after_import:.2f} MB")

# Build a small dummy model session to verify execution provider and thread options
session_options = ort.SessionOptions()
session_options.intra_op_num_threads = 4
session_options.inter_op_num_threads = 1
session_options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL

print("Available execution providers:", ort.get_available_providers())

print("Memory check completed successfully.")
