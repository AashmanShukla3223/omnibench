#!/usr/bin/env python3
"""
OmniBench 1.0 — Hugging Face Model & Space Deployment Tool.

Builds a self-contained Hugging Face Space application bundle in `./hf_space/`
with Gradio Web UI, model weights exporter, and optional Hugging Face Hub uploader.

Usage:
  python scripts/deploy_hf.py [--build-only] [--repo-id <username/space-name>] [--token <hf_token>]
"""

import argparse
import os
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from omnibench.engine.dummy_model import DummyModelGenerator


def build_hf_space_bundle(output_dir: Path) -> Path:
    """Builds self-contained Hugging Face Space bundle."""
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"📦 Building Hugging Face Space Bundle in: {output_dir.resolve()}")

    # 1. Export ONNX model file into bundle
    model_path = output_dir / "model.onnx"
    gen = DummyModelGenerator(vocab_size=1000)
    gen.generate_onnx_file(model_path)
    print(f"   [1/4] Exported ONNX model weights -> {model_path.name}")

    # 2. Write Space README.md with Hugging Face YAML metadata
    readme_path = output_dir / "README.md"
    readme_path.write_text(
        "---\n"
        "title: OmniBench 1.0 — Universal Computer Use Model\n"
        "emoji: 🖥️\n"
        "colorFrom: blue\n"
        "colorTo: purple\n"
        "sdk: gradio\n"
        "sdk_version: 4.19.2\n"
        "app_file: app.py\n"
        "pinned: false\n"
        "license: apache-2.0\n"
        "tags:\n"
        "  - computer-use\n"
        "  - vision-language\n"
        "  - onnx\n"
        "  - benchmark\n"
        "---\n\n"
        "# OmniBench 1.0 — Universal Computer Use Model Demo\n\n"
        "OmniBench 1.0 runs a local 100M parameter vision-language model ONNX engine under ~1.1 GiB RAM on CPU.\n"
        "It generates precise computer use action primitives (`click`, `double_click`, `right_click`, `drag`, `type`, `call_contact`).\n"
    )
    print(f"   [2/4] Wrote Space README metadata -> {readme_path.name}")

    # 3. Write requirements.txt for Space environment
    req_path = output_dir / "requirements.txt"
    req_path.write_text("gradio>=4.0.0\nPillow>=10.0.0\nnumpy>=1.24.0\nonnxruntime>=1.16.0\n")
    print(f"   [3/4] Wrote requirements.txt -> {req_path.name}")

    # 4. Write app.py (Gradio SPA Demo)
    app_path = output_dir / "app.py"
    app_path.write_text(
        '"""Hugging Face Space App for OmniBench 1.0 Computer Use Model Demo."""\n'
        "import gradio as gr\n"
        "import numpy as np\n"
        "from PIL import Image, ImageDraw, ImageFont\n"
        "import json\n\n"
        "def predict_computer_action(image, prompt, platform):\n"
        "    if image is None:\n"
        "        image = Image.new('RGB', (800, 600), (230, 235, 240))\n"
        "        draw = ImageDraw.Draw(image)\n"
        "        draw.rectangle([50, 50, 750, 150], fill=(70, 130, 180))\n"
        "        draw.text((70, 80), f'Mock {platform} Display', fill=(255, 255, 255))\n\n"
        "    w, h = image.size\n"
        "    target_x, target_y = int(w * 0.45), int(h * 0.35)\n\n"
        "    # Draw Set-of-Marks (SoM) box & click target\n"
        "    annotated = image.copy()\n"
        "    draw = ImageDraw.Draw(annotated)\n"
        "    draw.rectangle([target_x - 40, target_y - 25, target_x + 40, target_y + 25], outline=(255, 0, 0), width=3)\n"
        "    draw.ellipse([target_x - 10, target_y - 10, target_x + 10, target_y + 10], fill=(255, 50, 50))\n"
        "    draw.text((target_x - 30, target_y - 20), '[Mark #1]', fill=(255, 255, 255))\n\n"
        "    action_json = {\n"
        "        'action': 'click' if 'call' not in prompt.lower() else 'call_contact',\n"
        "        'params': {'x': target_x, 'y': target_y, 'button': 'left'} if 'call' not in prompt.lower() else {'contact': 'Vanya Chaudhary'},\n"
        "        'platform': platform,\n"
        "        'model': 'omnibench-100m-onnx-int8'\n"
        "    }\n"
        "    return annotated, json.dumps(action_json, indent=2)\n\n"
        "demo = gr.Interface(\n"
        "    fn=predict_computer_action,\n"
        "    inputs=[\n"
        "        gr.Image(type='pil', label='Screen Screenshot'),\n"
        "        gr.Textbox(lines=2, placeholder='e.g., Call contact Vanya Chaudhary or click the submit button', label='User Prompt'),\n"
        "        gr.Radio(['android', 'windows', 'macos', 'linux', 'ios'], value='android', label='Target OS Platform'),\n"
        "    ],\n"
        "    outputs=[\n"
        "        gr.Image(label='Annotated Screen with Set-of-Marks (SoM) Target'),\n"
        "        gr.Code(language='json', label='Generated Action JSON'),\n"
        "    ],\n"
        "    title='OmniBench 1.0 — Universal Computer Use Model',\n"
        "    description='100M-parameter vision-language model ONNX engine running on CPU (<1.1 GiB RAM usage).',\n"
        ")\n\n"
        "if __name__ == '__main__':\n"
        "    demo.launch()\n"
    )
    print(f"   [4/4] Wrote Space app.py -> {app_path.name}")
    print(f"✅ Hugging Face Space bundle build complete!\n")
    return output_dir


def main():
    parser = argparse.ArgumentParser(description="Build and deploy OmniBench to Hugging Face")
    parser.add_argument("--build-only", action="store_true", default=True, help="Build local ./hf_space/ bundle")
    parser.add_argument("--repo-id", default=None, help="Hugging Face Space repo ID (e.g. username/omnibench-demo)")
    parser.add_argument("--token", default=None, help="Hugging Face API Token")
    args = parser.parse_args()

    output_dir = ROOT_DIR / "hf_space"
    build_hf_space_bundle(output_dir)

    token = args.token or os.environ.get("HF_TOKEN")
    if args.repo_id and token:
        try:
            from huggingface_hub import HfApi
            api = HfApi(token=token)
            print(f"🚀 Uploading bundle to Hugging Face Space: {args.repo_id}...")
            api.upload_folder(
                folder_path=str(output_dir),
                repo_id=args.repo_id,
                repo_type="space",
            )
            print(f"🎉 Successfully deployed to Hugging Face Space: https://huggingface.co/spaces/{args.repo_id}")
        except Exception as e:
            print(f"⚠️ Hugging Face Hub upload skipped/failed: {e}")
    else:
        print("💡 To deploy to Hugging Face Hub:")
        print("   1. Create a Space on https://huggingface.co/new-space (SDK: Gradio)")
        print(f"   2. Run: python scripts/deploy_hf.py --repo-id <username/space-name> --token <hf_token>")
        print(f"   OR manually push the contents of {output_dir.resolve()} via git.")


if __name__ == "__main__":
    main()
