#!/usr/bin/env bash
# YingMusic-SVC setup for Linux / macOS.
# Creates a venv, installs dependencies, ffmpeg, and downloads all models.
set -euo pipefail
cd "$(dirname "$0")"

echo "== YingMusic-SVC setup (Linux/macOS) =="

# Download mirror: cn (ModelScope + hf-mirror + Tsinghua PyPI) or official (huggingface.co + PyPI.org).
# Usage:  ./setup.sh            -> official (default, suitable outside China)
#         ./setup.sh cn         -> China mirrors
MIRROR="${1:-official}"
case "$MIRROR" in
  cn|official) ;;
  *) echo "Unknown mirror '$MIRROR'. Valid: cn / official"; exit 1 ;;
esac
echo "Download mirror: $MIRROR"

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

# 3. Dependencies. requirements.txt hard-codes Tsinghua PyPI + Aliyun cu124 wheels,
#    and those in-file options OVERRIDE any -i passed on the command line.
#    For the official mirror we strip them out and use PyPI.org + pytorch.org instead.
"$VENVPY" -m pip install --upgrade pip
if [ "$MIRROR" = "official" ]; then
  TMPREQ=".requirements.install.txt"
  grep -vE '^[[:space:]]*--(index-url|find-links)' requirements.txt > "$TMPREQ" || true
  "$VENVPY" -m pip install -r "$TMPREQ" \
    --index-url https://pypi.org/simple \
    --extra-index-url https://download.pytorch.org/whl/cu124
  rm -f "$TMPREQ"
else
  "$VENVPY" -m pip install -r requirements.txt
fi

# 4. ffmpeg / sox (Debian/Ubuntu). Other distros: install via your package manager.
if command -v apt >/dev/null 2>&1; then
  sudo apt update && sudo apt install -y ffmpeg sox libsox-fmt-all || true
fi

# 5. Models (main weights + runtime models), following the same mirror choice.
"$VENVPY" download_models.py --mirror "$MIRROR"

echo ""
echo "Setup complete. Start the Web UI with:"
echo "  .venv/bin/python gradio_app.py"
echo "Then open http://127.0.0.1:30911"
