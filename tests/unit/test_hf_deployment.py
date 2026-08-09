"""Unit tests for Hugging Face model & Space deployment builder."""

import pytest
from pathlib import Path
from scripts.deploy_hf import build_hf_space_bundle


class TestHFDeployment:
    def test_build_hf_space_bundle(self, tmp_path):
        out = build_hf_space_bundle(tmp_path)
        assert (out / "app.py").exists()
        assert (out / "README.md").exists()
        assert (out / "requirements.txt").exists()
        assert (out / "model.onnx").exists()

        readme_text = (out / "README.md").read_text()
        assert "sdk: gradio" in readme_text
        assert "OmniBench" in readme_text

        app_text = (out / "app.py").read_text()
        assert "predict_computer_action" in app_text
        assert "gradio" in app_text
