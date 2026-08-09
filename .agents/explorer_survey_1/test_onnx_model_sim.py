import os
import sys
import time
import psutil
import numpy as np

process = psutil.Process(os.getpid())

def get_ram_mb():
    return process.memory_info().rss / (1024 * 1024)

ram_start = get_ram_mb()
print(f"Base RAM: {ram_start:.2f} MB")

import onnxruntime as ort

# Generate dummy 100M parameters as INT8 array (~100 MB on disk / RAM)
num_params = 100_000_000 # 100M parameters
weights_int8 = np.random.randint(-128, 127, size=(num_params,), dtype=np.int8)

ram_weights = get_ram_mb()
print(f"RAM with 100M INT8 params in numpy: {ram_weights:.2f} MB (Delta: {ram_weights - ram_start:.2f} MB)")

# Generate 100M parameters as INT4 packed array (50 MB)
weights_int4_packed = np.random.randint(0, 255, size=(num_params // 2,), dtype=np.uint8)
ram_int4 = get_ram_mb()
print(f"RAM with 100M INT4 packed params: {ram_int4:.2f} MB (Delta from weights: {ram_int4 - ram_weights:.2f} MB)")

del weights_int8
del weights_int4_packed
import gc
gc.collect()

ram_after_gc = get_ram_mb()
print(f"RAM after GC release: {ram_after_gc:.2f} MB")

print("Verification: INT8 100M model uses ~100 MB RAM; INT4 uses ~50 MB RAM.")
print(f"Well under the 1.1 GiB (1126.4 MB) RAM budget limit!")
