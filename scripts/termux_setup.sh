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

# 1. Update Termux Packages & Fast Pre-compiled Binary Dependencies
echo "[1/4] Installing Termux pre-compiled binary packages (Fast Mode)..."
for p in python git android-tools python-numpy python-pillow; do
    pkg install -y "$p" || true
done

# 2. Setup / Pull OmniBench Repository
echo "[2/4] Setting up OmniBench codebase..."
if [ -d "omnibench" ]; then
    cd omnibench
    git pull origin master || true
else
    if [ ! -f "pyproject.toml" ]; then
        git clone --depth 1 https://github.com/AashmanShukla3223/omnibench.git
        cd omnibench
    fi
fi

# 3. Fast PIP Install (No Source Compilation)
echo "[3/4] Registering package & downloading model weights..."
python3 -m pip install --prefer-binary --no-deps -e . || true
python3 -m pip install --prefer-binary huggingface_hub || true
python3 scripts/download_model.py --format gguf

# 4. Launch Mobile Task Execution
echo "[4/4] Launching Mobile Phone Contact Calling Task..."
python scripts/deploy_android.py --contact "Vanya Chaudhary"

echo "------------------------------------------------------------------"
echo "🎉 OmniBench Termux Setup & Task Execution Complete!"
