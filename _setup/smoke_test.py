"""Offline smoke test: load every model the SVC inference pipeline needs.

Run from the project root:
    .venv\\Scripts\\python.exe _setup\\smoke_test.py

HF_HUB_OFFLINE=1 guarantees the test fails loudly if any cached file is missing,
instead of silently downloading from the internet.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
os.environ.setdefault("HF_HOME", str(ROOT / "checkpoints"))
os.environ.setdefault("HF_HUB_CACHE", str(ROOT / "checkpoints" / "hf_cache"))
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"

import types  # noqa: E402

import torch  # noqa: E402

from my_inference import load_models_api  # noqa: E402

args = types.SimpleNamespace(
    checkpoint="checkpoints/YingMusic-SVC-full.pt",
    config="configs/YingMusic-SVC.yml",
)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("torch:", torch.__version__, "| device:", device, flush=True)
bundle = load_models_api(args, device=device)
print("SMOKE TEST PASSED - all models loaded from local cache", flush=True)
print("bundle type:", type(bundle).__name__, flush=True)
