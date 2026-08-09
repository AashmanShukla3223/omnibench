"""
OmniBench Engine Preprocessor — public aliases and extended tokenizer.
Wraps the Preprocessor and KVCacheManager with convenient named exports.
"""

from omnibench.engine.preprocessor import Preprocessor, KVCacheManager
from typing import List, Union, Optional
from PIL import Image
import numpy as np

# Public alias
ScreenPreprocessor = Preprocessor


class TextTokenizer:
    """
    Simple character-level tokenizer aligned with OmniBench 100M dummy model vocab.
    For production, replace with a real BPE or SentencePiece tokenizer.
    """

    def __init__(self, vocab_size: int = 1000, max_length: int = 512) -> None:
        self.vocab_size = vocab_size
        self.max_length = max_length

    def encode(self, text: str) -> List[int]:
        """Encode text to list of token ids."""
        tokens = [ord(c) % self.vocab_size for c in text.strip()]
        return tokens[: self.max_length]

    def decode(self, token_ids: List[int]) -> str:
        """Decode token ids back to string (best-effort)."""
        chars = []
        for tid in token_ids:
            c = tid % 128
            if 32 <= c < 127:
                chars.append(chr(c))
            else:
                chars.append(" ")
        return "".join(chars)

    def encode_numpy(self, text: str) -> "np.ndarray":
        """Return encoded token ids as int64 numpy array [1, seq_len]."""
        ids = self.encode(text)
        return np.array([ids], dtype=np.int64)


__all__ = ["ScreenPreprocessor", "TextTokenizer", "Preprocessor", "KVCacheManager"]
