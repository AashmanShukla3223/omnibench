#!/usr/bin/env python3
"""
OmniBench 1.0 — Direct HTTP Model Weights Downloader.

Downloads GGUF, ONNX, and MLX model weights directly from Hugging Face Hub CDN.
Requires ZERO external pip packages (uses Python standard library urllib.request).

Usage:
  python scripts/download_model.py [--format gguf|onnx|mlx]
"""

import argparse
import os
import sys
import urllib.request
from pathlib import Path


def download_with_progress(url: str, output_path: str):
    """Download URL to file path using urllib with visual progress feedback."""
    print(f"📥 Streaming download directly from HF CDN:\n   {url}")

    def reporthook(blocknum, blocksize, totalsize):
        readSoFar = blocknum * blocksize
        if totalsize > 0:
            percent = readSoFar * 100 / totalsize
            sys.stdout.write(f"\r   Progress: {percent:.1f}% ({readSoFar}/{totalsize} bytes)")
            sys.stdout.flush()
        else:
            sys.stdout.write(f"\r   Downloaded: {readSoFar} bytes")
            sys.stdout.flush()

    try:
        urllib.request.urlretrieve(url, output_path, reporthook=reporthook)
        sys.stdout.write("\n")
        print(f"✅ Successfully downloaded -> {output_path}")
    except Exception as e:
        sys.stdout.write("\n")
        # Try fallback using system curl if available
        print(f"⚠️  urllib failed ({e}), attempting system curl fallback...")
        ret = os.system(f"curl -sSL -o '{output_path}' '{url}'")
        if ret == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            print(f"✅ Successfully downloaded via curl -> {output_path}")
        else:
            print(f"❌ Download failed: {e}")
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Directly download OmniBench model weights from Hugging Face CDN")
    parser.add_argument("--format", choices=["gguf", "onnx", "mlx"], default="gguf", help="Model format to download (default: gguf)")
    parser.add_argument("--repo-id", default="AashmanShukla3223/omnibench-1.0-100m", help="Hugging Face Model Repo ID")
    args = parser.parse_args()

    filename = f"model.{args.format}" if args.format != "mlx" else "mlx/weights.npz"
    cdn_url = f"https://huggingface.co/{args.repo_id}/resolve/main/{filename}"
    
    download_with_progress(cdn_url, filename)


if __name__ == "__main__":
    main()
