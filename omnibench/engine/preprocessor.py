"""Image & text input preprocessing and layer-wise KV cache manager for ONNXLocalEngine."""

import io
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from PIL import Image


class Preprocessor:
    """Formats visual screenshots and text prompts for vision-language ONNX inference."""

    def __init__(
        self,
        target_image_size: Tuple[int, int] = (224, 224),
        mean: Tuple[float, float, float] = (0.485, 0.456, 0.406),
        std: Tuple[float, float, float] = (0.229, 0.224, 0.225),
    ) -> None:
        self.target_image_size = target_image_size
        self.mean = np.array(mean, dtype=np.float32).reshape(1, 3, 1, 1)
        self.std = np.array(std, dtype=np.float32).reshape(1, 3, 1, 1)

    def preprocess_image(
        self, image: Union[bytes, Image.Image, np.ndarray]
    ) -> np.ndarray:
        """Converts input image to float32 RGB tensor array of shape (1, 3, H, W)."""
        if isinstance(image, bytes):
            pil_img = Image.open(io.BytesIO(image)).convert("RGB")
        elif isinstance(image, Image.Image):
            pil_img = image.convert("RGB")
        elif isinstance(image, np.ndarray):
            if image.ndim == 2:
                pil_img = Image.fromarray(image).convert("RGB")
            elif image.ndim == 3:
                if image.shape[0] in (1, 3):
                    # CHW format -> HWC format
                    arr = np.transpose(image, (1, 2, 0))
                else:
                    arr = image
                pil_img = Image.fromarray(arr.astype(np.uint8)).convert("RGB")
            else:
                raise ValueError(f"Unsupported numpy image array dimensions: {image.ndim}")
        else:
            raise ValueError(f"Unsupported image type: {type(image)}")

        # Resize to target (224, 224)
        pil_img = pil_img.resize(self.target_image_size, Image.Resampling.BILINEAR)
        img_np = np.array(pil_img, dtype=np.float32) / 255.0  # HWC

        # Transpose HWC -> CHW
        chw = np.transpose(img_np, (2, 0, 1))  # (3, H, W)
        batch = np.expand_dims(chw, axis=0)    # (1, 3, H, W)

        # Normalize with mean and std
        normalized = (batch - self.mean) / self.std
        return normalized.astype(np.float32)

    def preprocess_text(self, text: str, max_length: int = 512) -> np.ndarray:
        """Tokenizes text string into int64 array of shape (1, seq_len)."""
        if not isinstance(text, str):
            text = str(text)
        
        cleaned = text.strip()
        if not cleaned:
            # Fallback to single padding token if text is empty
            tokens = [1]
        else:
            # Standard character/word encoding for synthetic/tokenizer fallback
            tokens = [ord(char) % 1000 for char in cleaned]

        tokens = tokens[:max_length]
        return np.array([tokens], dtype=np.int64)

    def process_inputs(
        self,
        prompt: str,
        images: Optional[List[Union[bytes, Image.Image, np.ndarray]]] = None,
    ) -> Dict[str, np.ndarray]:
        """Returns preprocessed input tensor map containing input_ids, attention_mask, and pixel_values."""
        input_ids = self.preprocess_text(prompt)
        attention_mask = np.ones_like(input_ids, dtype=np.int64)

        result: Dict[str, np.ndarray] = {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
        }

        if images and len(images) > 0:
            pixel_values = self.preprocess_image(images[0])
            result["pixel_values"] = pixel_values
        else:
            # Provide dummy pixel_values tensor if required by VLM model graph
            result["pixel_values"] = np.zeros(
                (1, 3, self.target_image_size[0], self.target_image_size[1]),
                dtype=np.float32,
            )

        return result


class KVCacheManager:
    """Manages layer-wise Key/Value tensor cache with memory footprint assertions."""

    def __init__(
        self,
        max_batch_size: int = 1,
        num_heads: int = 8,
        head_dim: int = 64,
        max_seq_len: int = 1024,
        dtype: np.dtype = np.float32,
    ) -> None:
        self.max_batch_size = max_batch_size
        self.num_heads = num_heads
        self.head_dim = head_dim
        self.max_seq_len = max_seq_len
        self.dtype = dtype
        self.cache_keys: Dict[int, np.ndarray] = {}
        self.cache_values: Dict[int, np.ndarray] = {}

    def reset(self) -> None:
        """Clears all cached key and value tensors across all layers."""
        self.cache_keys.clear()
        self.cache_values.clear()

    def update(
        self, key_states: np.ndarray, value_states: np.ndarray, layer_idx: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Appends key_states and value_states for specified layer_idx and returns updated cache."""
        if layer_idx in self.cache_keys:
            existing_k = self.cache_keys[layer_idx]
            existing_v = self.cache_values[layer_idx]
            new_k = np.concatenate([existing_k, key_states], axis=-2)
            new_v = np.concatenate([existing_v, value_states], axis=-2)
        else:
            new_k = key_states
            new_v = value_states

        seq_len = new_k.shape[-2]
        if seq_len > self.max_seq_len:
            # Truncate sequence window to max_seq_len
            new_k = new_k[..., -self.max_seq_len:, :]
            new_v = new_v[..., -self.max_seq_len:, :]

        self.cache_keys[layer_idx] = new_k
        self.cache_values[layer_idx] = new_v
        return new_k, new_v

    def get_cache(
        self, layer_idx: int
    ) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """Retrieves cached key and value states for layer_idx."""
        return self.cache_keys.get(layer_idx), self.cache_values.get(layer_idx)

    def get_memory_footprint(self) -> int:
        """Returns total memory consumption of stored KV caches in bytes."""
        total_bytes = sum(k.nbytes for k in self.cache_keys.values())
        total_bytes += sum(v.nbytes for v in self.cache_values.values())
        return total_bytes
