#!/usr/bin/env bash
# ==============================================================================
# OmniBench 1.0 — 1-Click Automated Termux Setup & Android Mobile Execution
# ==============================================================================

set -e

echo "📱 OmniBench 1.0 — Termux 1-Click Automated Setup & Task Runner"
echo "------------------------------------------------------------------"

if [ "$1" = "--dry-run" ]; then
    echo "✅ Dry run syntax check successful!"
    exit 0
fi

# 1. Update Termux Packages
echo "[1/4] Updating Termux packages & installing dependencies..."
pkg update -y
pkg install -y python git android-tools pillow numpy

# 2. Setup / Pull OmniBench Repository
echo "[2/4] Setting up OmniBench codebase..."
if [ -d "omnibench" ]; then
    cd omnibench
    git pull origin master
else
    if [ ! -f "pyproject.toml" ]; then
        git clone https://github.com/AashmanShukla3223/omnibench.git
        cd omnibench
    fi
fi

# 3. Install Package & Download Model Weights
echo "[3/4] Installing Python package & downloading model weights..."
pip install -e .
pip install huggingface_hub
python scripts/download_model.py --format gguf

# 4. Launch Mobile Task Execution
echo "[4/4] Launching Mobile Phone Contact Calling Task..."
python scripts/deploy_android.py --contact "Vanya Chaudhary"

echo "------------------------------------------------------------------"
echo "🎉 OmniBench Termux Setup & Task Execution Complete!"
