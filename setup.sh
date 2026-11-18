#!/usr/bin/env bash
# YingMusic-SVC setup for Linux / macOS.
# Creates a venv, installs dependencies, ffmpeg, and downloads all models.
set -euo pipefail
cd "$(dirname "$0")"

echo "== YingMusic-SVC setup (Linux/macOS) =="

# 1. Python 3.10
PY="$(command -v python3.10 || true)"
if [ -z "$PY" ]; then
  echo "Python 3.10 not found. Install it first, e.g.:"
  echo "  conda create -n ymsvc python=3.10 && conda activate ymsvc"
  echo "  (or use your distro's python3.10 package)"
  exit 1
fi
echo "Using Python: $PY"

# 2. Virtual environment
[ -x ".venv/bin/python" ] || "$PY" -m venv .venv
VENVPY=".venv/bin/python"

# 3. Dependencies (requirements.txt pins torch 2.4.0+cu124; adjust index for your region)
"$VENVPY" -m pip install --upgrade pip
"$VENVPY" -m pip install -r requirements.txt

# 4. ffmpeg / sox (Debian/Ubuntu). Other distros: install via your package manager.
if command -v apt >/dev/null 2>&1; then
  sudo apt update && sudo apt install -y ffmpeg sox libsox-fmt-all || true
fi

# 5. Models. Use --mirror cn for China mirrors (ModelScope + hf-mirror),
#    or --mirror official for HuggingFace. Default here is official for non-CN users.
MIRROR="${1:-official}"
"$VENVPY" download_models.py --mirror "$MIRROR"

echo ""
echo "Setup complete. Start the Web UI with:"
echo "  .venv/bin/python gradio_app.py"
echo "Then open http://127.0.0.1:30911"
