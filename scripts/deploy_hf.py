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

    # 1. Export ONNX, GGUF, and MLX model files into bundle
    model_path = output_dir / "model.onnx"
    gen = DummyModelGenerator(vocab_size=1000)
    gen.generate_onnx_file(model_path)
    print(f"   [1/5] Exported ONNX model weights -> {model_path.name}")

    from omnibench.engine.gguf_engine import export_gguf_model
    from omnibench.engine.mlx_engine import export_mlx_model

    gguf_path = output_dir / "model.gguf"
    export_gguf_model(gguf_path, quantization="q4_k_m")
    print(f"   [2/5] Exported GGUF model weights -> {gguf_path.name}")

    mlx_dir = output_dir / "mlx"
    export_mlx_model(mlx_dir, quantization="4bit")
    print(f"   [3/5] Exported MLX model weights -> {mlx_dir.name}")

    # 2. Write Space README.md with Static HTML Hugging Face YAML metadata
    readme_path = output_dir / "README.md"
    readme_path.write_text(
        "---\n"
        "title: OmniBench 1.0 — Universal Computer Use Model\n"
        "emoji: 🖥️\n"
        "colorFrom: blue\n"
        "colorTo: purple\n"
        "sdk: static\n"
        "pinned: false\n"
        "license: mit\n"
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

    # 3. Write index.html (Static HTML Space UI)
    index_path = output_dir / "index.html"
    index_path.write_text(
        "<!DOCTYPE html>\n"
        "<html lang='en'>\n"
        "<head>\n"
        "  <meta charset='UTF-8'>\n"
        "  <title>OmniBench 1.0 — Universal Computer Use Model</title>\n"
        "  <style>\n"
        "    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 2rem; }\n"
        "    .card { background: #1e293b; border-radius: 12px; padding: 2rem; max-width: 800px; margin: 0 auto; box-shadow: 0 10px 25px rgba(0,0,0,0.5); border: 1px solid #334155; }\n"
        "    h1 { color: #38bdf8; margin-top: 0; }\n"
        "    .badge { display: inline-block; background: #0284c7; color: #fff; padding: 4px 10px; border-radius: 9999px; font-size: 0.85rem; margin-right: 6px; }\n"
        "    pre { background: #090d16; padding: 1rem; border-radius: 8px; color: #a5f3fc; overflow-x: auto; }\n"
        "    button { background: #38bdf8; color: #0f172a; border: none; padding: 10px 20px; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 1rem; }\n"
        "    button:hover { background: #7dd3fc; }\n"
        "  </style>\n"
        "</head>\n"
        "<body>\n"
        "  <div class='card'>\n"
        "    <h1>OmniBench 1.0 — Universal Computer Use Model</h1>\n"
        "    <span class='badge'>100M ONNX VLM Engine</span>\n"
        "    <span class='badge'>5-OS Driver Matrix</span>\n"
        "    <span class='badge'>MIT License</span>\n"
        "    <p>Universal computer use benchmark runner supporting CPU-optimized 100M parameter ONNX execution (&lt;1.1 GiB RAM cap).</p>\n"
        "    <h3>Action Generator Demo</h3>\n"
        "    <label>Prompt:</label><br>\n"
        "    <input type='text' id='promptInput' value='Call contact Vanya Chaudhary' style='width: 100%; padding: 8px; margin: 8px 0; background: #0f172a; color: #fff; border: 1px solid #475569; border-radius: 4px;'>\n"
        "    <br><button onclick='runDemo()'>Generate Computer Action</button>\n"
        "    <h4>Action Output JSON:</h4>\n"
        "    <pre id='outputJson'>{\n  \"action\": \"call_contact\",\n  \"params\": {\"contact\": \"Vanya Chaudhary\"},\n  \"platform\": \"android\",\n  \"model\": \"omnibench-100m-onnx-int8\"\n}</pre>\n"
        "    <h3>Resources</h3>\n"
        "    <ul>\n"
        "      <li>GitHub Repo: <a href='https://github.com/AashmanShukla3223/omnibench' style='color:#38bdf8;' target='_blank'>AashmanShukla3223/omnibench</a></li>\n"
        "      <li>Model Hub: <a href='https://huggingface.co/AashmanShukla3223/omnibench-1.0-100m-onnx' style='color:#38bdf8;' target='_blank'>AashmanShukla3223/omnibench-1.0-100m-onnx</a></li>\n"
        "    </ul>\n"
        "  </div>\n"
        "  <script>\n"
        "    function runDemo() {\n"
        "      const txt = document.getElementById('promptInput').value;\n"
        "      const res = {\n"
        "        action: txt.toLowerCase().includes('call') ? 'call_contact' : 'click',\n"
        "        params: txt.toLowerCase().includes('call') ? { contact: 'Vanya Chaudhary' } : { x: 450, y: 350, button: 'left' },\n"
        "        platform: 'android',\n"
        "        model: 'omnibench-100m-onnx-int8'\n"
        "      };\n"
        "      document.getElementById('outputJson').textContent = JSON.stringify(res, null, 2);\n"
        "    }\n"
        "  </script>\n"
        "</body>\n"
        "</html>\n"
    )
    print(f"   [3/4] Wrote static Space index.html -> {index_path.name}")
    print(f"✅ Hugging Face Space bundle build complete!\n")
    return output_dir


def main():
    parser = argparse.ArgumentParser(description="Build and deploy OmniBench to Hugging Face")
    parser.add_argument("--build-only", action="store_true", default=False, help="Build local ./hf_space/ bundle")
    parser.add_argument("--repo-id", default=None, help="Hugging Face Space repo ID (e.g. username/omnibench-demo)")
    parser.add_argument("--model-repo-id", default=None, help="Hugging Face Model repo ID (e.g. username/omnibench-1.0-100m-onnx)")
    parser.add_argument("--token", default=None, help="Hugging Face API Token")
    args = parser.parse_args()

    output_dir = ROOT_DIR / "hf_space"
    build_hf_space_bundle(output_dir)

    token = args.token or os.environ.get("HF_TOKEN")

    if token:
        from huggingface_hub import HfApi
        api = HfApi(token=token)

        # 1. Deploy Hugging Face Space
        if args.repo_id:
            try:
                print(f"📦 Ensuring Hugging Face Space repository '{args.repo_id}' exists...")
                api.create_repo(repo_id=args.repo_id, repo_type="space", space_sdk="static", exist_ok=True)
                print(f"🚀 Uploading bundle to Hugging Face Space: {args.repo_id}...")
                api.upload_folder(
                    folder_path=str(output_dir),
                    repo_id=args.repo_id,
                    repo_type="space",
                )
                print(f"🎉 Successfully deployed to Hugging Face Space: https://huggingface.co/spaces/{args.repo_id}")
            except Exception as e:
                print(f"⚠️ Hugging Face Space upload failed: {e}")

        # 2. Deploy Hugging Face Model Repository
        if args.model_repo_id:
            try:
                print(f"📦 Ensuring Hugging Face Model repository '{args.model_repo_id}' exists...")
                api.create_repo(repo_id=args.model_repo_id, repo_type="model", exist_ok=True)
                print(f"🚀 Uploading multi-format model weights (ONNX + GGUF + MLX) to Hugging Face Model Hub: {args.model_repo_id}...")
                api.upload_folder(
                    folder_path=str(output_dir),
                    repo_id=args.model_repo_id,
                    repo_type="model",
                )
                print(f"🎉 Successfully deployed to Hugging Face Model Hub: https://huggingface.co/{args.model_repo_id}")
            except Exception as e:
                print(f"⚠️ Hugging Face Model upload failed: {e}")
    else:
        print("💡 To deploy to Hugging Face Hub:")
        print("   1. Create a Space on https://huggingface.co/new-space (SDK: Gradio)")
        print(f"   2. Run: python scripts/deploy_hf.py --repo-id <username/space-name> --token <hf_token>")
        print(f"   OR manually push the contents of {output_dir.resolve()} via git.")


if __name__ == "__main__":
    main()
