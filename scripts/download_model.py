#!/usr/bin/env python3
"""
OmniBench 1.0 — Model Weights Downloader.

Downloads GGUF, ONNX, and MLX model weights from Hugging Face Hub.

Usage:
  python scripts/download_model.py [--format gguf|onnx|mlx]
"""

import argparse
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from huggingface_hub import hf_hub_download


def main():
    parser = argparse.ArgumentParser(description="Download OmniBench model weights from Hugging Face Hub")
    parser.add_argument("--format", choices=["gguf", "onnx", "mlx"], default="gguf", help="Model format to download (default: gguf)")
    parser.add_argument("--repo-id", default="AashmanShukla3223/omnibench-1.0-100m", help="Hugging Face Model Repo ID")
    args = parser.parse_args()

    filename = f"model.{args.format}" if args.format != "mlx" else "mlx/weights.npz"
    print(f"📥 Downloading OmniBench 1.0 [{args.format.upper()}] model from {args.repo_id}...")

    try:
        local_path = hf_hub_download(repo_id=args.repo_id, filename=filename, local_dir=".")
        print(f"✅ Successfully downloaded model weights -> {local_path}")
    except Exception as e:
        print(f"❌ Download failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
