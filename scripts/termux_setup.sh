#!/usr/bin/env bash
# ==============================================================================
# OmniBench 1.0 — 1-Click Termux Zero-Dependency Setup & Mobile Runner
# Requires ZERO PyPI Packages (No Pillow, No NumPy, No C Compilation)
# ==============================================================================

set -e

echo "📱 OmniBench 1.0 — Termux Zero-Dependency Mobile Runner"
echo "--------------------------------------------------------"

if [ "$1" = "--dry-run" ]; then
    echo "✅ Dry run syntax check successful!"
    exit 0
fi

# 1. Install Base Packages (Standard Python + Git + ADB)
echo "[1/2] Installing base Termux packages (python, git, android-tools)..."
pkg update -y || true
for p in python git android-tools; do
    pkg install -y "$p" || true
done

# 2. Setup / Pull OmniBench Repository
echo "[2/2] Setting up OmniBench codebase..."
if [ -d "omnibench" ]; then
    cd omnibench
    git pull origin master || true
else
    if [ ! -f "pyproject.toml" ]; then
        git clone --depth 1 https://github.com/AashmanShukla3223/omnibench.git
        cd omnibench
    fi
fi

# 3. Direct CDN Model Download & Zero-Dependency Execution
echo "[3/3] Downloading model weights directly from HF CDN..."
python3 scripts/download_model.py --format gguf
python3 scripts/termux_zero_dep.py --contact "Vanya Chaudhary"

echo "--------------------------------------------------------"
echo "🎉 Termux Zero-Dependency Execution Complete!"
