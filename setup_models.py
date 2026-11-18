"""Pre-download the HuggingFace models required at runtime.

Uses hf-mirror.com (China mirror) by default. Run once after installing the
Python dependencies:

    .venv\\Scripts\\python.exe setup_models.py

The script is safe to re-run; already cached files are skipped.
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CKPT = ROOT / "checkpoints"
HF_CACHE = CKPT / "hf_cache"
CKPT.mkdir(exist_ok=True)
HF_CACHE.mkdir(parents=True, exist_ok=True)

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
os.environ["HF_HOME"] = str(CKPT)
os.environ["HF_HUB_CACHE"] = str(HF_CACHE)
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"

from huggingface_hub import hf_hub_download, snapshot_download  # noqa: E402

# (repo_id, filename or None for snapshot, cache_dir, allow_patterns)
# allow_patterns avoids pulling Whisper's TF/Flax/duplicate weights (several GB).
WHISPER_FILES = [
    "config.json",
    "preprocessor_config.json",
    "generation_config.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "vocab.json",
    "merges.txt",
    "special_tokens_map.json",
    "normalizer.json",
    "model.safetensors",
]

TARGETS = [
    ("lj1995/VoiceConversionWebUI", "rmvpe.pt", CKPT, None),
    ("funasr/campplus", "campplus_cn_common.bin", CKPT, None),
    (
        "nvidia/bigvgan_v2_44khz_128band_512x",
        None,
        HF_CACHE,
        ["config.json", "bigvgan_generator.pt"],
    ),
    ("openai/whisper-small", None, HF_CACHE, WHISPER_FILES),
]


def main():
    print("HF_ENDPOINT =", os.environ["HF_ENDPOINT"])
    print("HF cache    =", HF_CACHE)
    failed = []
    for repo, filename, cache, patterns in TARGETS:
        label = f"{repo} / {filename or '(filtered snapshot)'}"
        print(f"\n>>> {label}", flush=True)
        try:
            if filename:
                path = hf_hub_download(
                    repo_id=repo, filename=filename, cache_dir=str(cache)
                )
            else:
                path = snapshot_download(
                    repo_id=repo,
                    cache_dir=str(cache),
                    allow_patterns=patterns,
                )
            print("    OK ->", path, flush=True)
        except Exception as exc:  # noqa: BLE001
            print(f"    FAILED: {type(exc).__name__}: {exc}", flush=True)
            failed.append(label)

    print("\n=== summary ===")
    if failed:
        print("Not downloaded (runtime will retry automatically):")
        for item in failed:
            print("  -", item)
    else:
        print("All runtime models are cached. You are ready to go.")
    print("Tip: keep HF_ENDPOINT=https://hf-mirror.com in run_gradio.bat.")


if __name__ == "__main__":
    main()
