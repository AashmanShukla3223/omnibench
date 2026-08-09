# Handoff Report — Explorer 1: ONNX Engine & Preprocessor Architecture (`omnibench/engine/`)

## 1. Observation
- Directory Inspection: `/home/oh_my_macos27/OmniBench Computer Use/omnibench/` contains `drivers/` and `visual/`, but `omnibench/engine/` does NOT exist yet.
- Scope Requirements (`PROJECT.md` lines 12-15, `SCOPE.md` lines 7, 13-14):
  - Milestone M1 Feature 1: ONNX 100M Local Engine (`onnx_engine.py`, `dummy_model.py`). Must run on CPU under <1.1 GiB RAM.
  - Milestone M1 Feature 2: Model Preprocessor & KV Cache (`preprocessor.py`, `quantizer.py`). Input formatting, INT8/INT4 quantization, bounded KV cache.
- System Environment Verification (`.venv/bin/python`):
  - `onnxruntime` v1.28.0 with `CPUExecutionProvider` and `onnxruntime.quantization` verified active.
  - `onnx` v1.22.0 verified active.
  - `numpy`, `PIL` (Pillow), `pydantic` (v2), `psutil` verified active.
- RAM Bound: CPU RAM consumption must stay strictly below 1.1 GiB (1126.4 MiB).

## 2. Logic Chain
- **Step 1: Model Storage & Quantization Strategy (`dummy_model.py`, `quantizer.py`)**:
  - A 100M parameter model in standard float32 takes ~400 MB on disk/memory. Loaded raw into ORT without memory management, activations + workspace buffers could push RAM close to 800 MB - 1.2 GB.
  - Applying INT8 dynamic/weight quantization (`quantize_dynamic`) reduces weight footprint to ~100 MB. Applying INT4 reduces weights to ~50 MB.
  - `dummy_model.py` will programmatically construct a valid ONNX model graph containing Vision Projection layers and Transformer/Linear matrix multiplication blocks representing 100M parameters.
  - `quantizer.py` will encapsulate `ONNXQuantizer` using `onnxruntime.quantization` to perform dynamic/static INT8 and INT4 quantization, verifying model graph integrity after quantization.

- **Step 2: Preprocessing & Bounded KV Cache (`preprocessor.py`)**:
  - `ModelPreprocessor` handles image normalization (resizing PIL Image/bytes to `(3, 224, 224)` float32 array normalized to `[0, 1]` or ImageNet stats) and prompt text tokenization (padded token IDs and attention masks).
  - `KVCacheManager` maintains key-value state for generation steps with a hard upper bound on sequence length (`max_seq_len=1024`). It implements explicit truncation and `clear_cache()` methods to guarantee zero memory leakage across repeated task executions.

- **Step 3: Engine Execution & Memory Guard (`onnx_engine.py`)**:
  - `LocalONNXEngine` wraps ORT `InferenceSession` configured with `providers=['CPUExecutionProvider']` and optimized options (`enable_cpu_mem_arena=False`, thread limits `inter_op_num_threads=2`, `intra_op_num_threads=4`).
  - Uses `psutil.Process().memory_info().rss` to monitor RSS RAM in MiB.
  - Hard guard: If RSS exceeds 1126.4 MiB, triggers `gc.collect()`, clears KV cache, and raises `MemoryLimitExceededError` if memory remains over budget.
  - Standardized interface method `generate(prompt: str, images: list[bytes], max_tokens: int, temperature: float) -> dict` returning output compatible with `GatewayResponse` schema (`text`, `action_json`, `usage_tokens`, `latency_ms`, `provider_used`).

## 3. Caveats
- Synthetic vs. Downloaded Model Weights: For offline benchmark evaluation and self-contained execution without external weight downloads, the engine defaults to generating/loading the synthetic 100M ONNX model via `dummy_model.py`. The synthetic model maintains exact parameter count (100M) and graph structure.
- CPU Multithreading: Excessive OpenMP/INTEL thread count in ONNX Runtime can spike memory usage. Setting `inter_op_num_threads` and `intra_op_num_threads` explicitly keeps memory allocations controlled.

## 4. Conclusion & Detailed Implementation Strategy
The `omnibench/engine/` module should be implemented with the following structure:

### File Structure & Class Blueprint
1. `omnibench/engine/__init__.py`:
   - Exports: `LocalONNXEngine`, `ModelPreprocessor`, `KVCacheManager`, `ONNXQuantizer`, `generate_dummy_100m_onnx_model`, `MemoryLimitExceededError`.
2. `omnibench/engine/dummy_model.py`:
   - `generate_dummy_100m_onnx_model(output_path: str = "models/dummy_100m.onnx", quantize_mode: str = "INT8") -> str`:
     - Creates ONNX model graph with `onnx.helper`.
     - Inputs: `image_tensor` `[1, 3, 224, 224]`, `input_ids` `[1, seq_len]`.
     - Initializers: 100M parameters across weight matrices.
     - Outputs: `logits` `[1, vocab_size]`.
3. `omnibench/engine/quantizer.py`:
   - `class ONNXQuantizer`:
     - `quantize_model(input_path: str, output_path: str, quant_format: str = "INT8") -> str`
     - `get_model_size_mb(model_path: str) -> float`
     - `verify_quantized_model(model_path: str) -> bool`
4. `omnibench/engine/preprocessor.py`:
   - `class ModelPreprocessor`:
     - `preprocess_image(image_input: bytes | PIL.Image.Image | np.ndarray, target_size=(224, 224)) -> np.ndarray`
     - `preprocess_text(prompt: str, max_length: int = 512) -> tuple[np.ndarray, np.ndarray]`
     - `encode_inputs(prompt: str, images: list) -> dict[str, np.ndarray]`
   - `class KVCacheManager`:
     - `initialize_cache(num_layers: int, num_heads: int, head_dim: int)`
     - `update_cache(layer_idx: int, k: np.ndarray, v: np.ndarray) -> tuple[np.ndarray, np.ndarray]`
     - `clear_cache()`
     - `get_memory_usage_mb() -> float`
5. `omnibench/engine/onnx_engine.py`:
   - `class MemoryLimitExceededError(Exception)`
   - `class LocalONNXEngine`:
     - `__init__(model_path: str | None = None, max_ram_mib: float = 1126.4, quant_mode: str = "INT8")`
     - `generate(prompt: str, images: list[bytes] = [], max_tokens: int = 128, temperature: float = 0.7) -> dict`
     - `get_memory_stats() -> dict`
     - `close()`

## 5. Verification Method
- Verification Command for Memory Guard and Inference Execution:
  ```bash
  .venv/bin/python -c "
  from omnibench.engine.onnx_engine import LocalONNXEngine
  engine = LocalONNXEngine()
  res = engine.generate('Click on the search bar', images=[])
  stats = engine.get_memory_stats()
  print('Memory stats:', stats)
  assert stats['current_rss_mb'] < 1126.4, f'Memory limit exceeded: {stats[\"current_rss_mb\"]} MiB'
  assert 'text' in res and 'provider_used' in res
  print('ONNX Engine Verification PASSED!')
  "
  ```
- Invalidation Condition: Failure to initialize ONNX Runtime session, memory usage exceeding 1126.4 MiB RAM during generation, or invalid response dictionary format.
