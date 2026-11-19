# YingMusic-SVC · Enhanced Distribution

**English** | [简体中文](README.md)

> An enhanced fork of [GiantAILab/YingMusic-SVC](https://github.com/GiantAILab/YingMusic-SVC):
> **one-click Windows installation + fully offline runtime + bilingual UI + reference timbre library + mixing fixes + a complete set of Mainland-China mirrors**.
> The source repository does not directly store model weights; the Windows Release installer bundles all models, while source installations download them through the setup scripts.

**YingMusic-SVC** is a real-world robust zero-shot singing voice conversion (Zero-Shot SVC) framework. It combines continual pre-training, robust supervised fine-tuning, and Flow-GRPO reinforcement learning to maintain stable timbre similarity and intelligibility in real songs with accompaniment and harmony interference. Paper: [arXiv:2512.04793](https://arxiv.org/abs/2512.04793).

---

## 📥 Download and Install (For Most Users)

**Current version: [v1.0.0](https://github.com/yonye1080/YingMusic-SVC-Launcher/releases/tag/v1.0.0)** (published, not a draft).

> The GitHub repository is currently **private**, so the Release is visible only to users with repository access. Public distribution requires changing the repository visibility separately. The Release contains 4 installer files and 1 `SHA256SUMS.txt` file.

The Windows installer bundles Python, dependencies, FFmpeg, and all models. **After installation, no additional model downloads are required and the application runs without internet access.**

1. Download the following **4 files** from the Release and place them in the same folder:
   - `YingMusic-SVC-Launcher-1.0.0-Setup.exe`
   - `YingMusic-SVC-Launcher-1.0.0-Setup-1.bin`
   - `YingMusic-SVC-Launcher-1.0.0-Setup-2.bin`
   - `YingMusic-SVC-Launcher-1.0.0-Setup-3.bin`
2. Run `Setup.exe` and follow the wizard. Administrator privileges are not required. Missing any `.bin` file will make the installation fail.
3. Start the application from the Start Menu or desktop shortcut, then open <http://127.0.0.1:30911> in a browser.

| Item | Measured for the current release |
|---|---|
| Download size | **5.34 GB / 4.98 GiB** |
| Installed size | **about 8.15 GiB** |
| Default install location | `%LocalAppData%\Programs\YingMusic-SVC-Launcher` |
| OS | Windows 10 / 11, 64-bit |
| GPU | NVIDIA recommended; driver r550 or newer is suggested (CUDA 12.4 support) |

The Release also provides `SHA256SUMS.txt` to verify the integrity of the four installer files. The installer is not code-signed. If SmartScreen shows “Unknown publisher” on first launch, verify the file source and hashes, then choose “More info → Run anyway”.

**Current validation status**: clean silent installation, an actual audio conversion from the installed directory, startup from a working directory outside the program folder, consecutive conversions, repeated separation, and complete uninstallation were all tested on Windows with an RTX 4060 8GB GPU. No installation directory, shortcut, or cache residue remained. A separate fully clean Windows machine without any prior development environment has not yet been tested.

---

## ✨ Enhancements Over Upstream

| Enhancement | Description |
|---|---|
| 🪟 One-click Windows installation | A complete offline installer is provided in Releases. For source installs, `setup_windows.bat` configures the environment, deploys FFmpeg, and downloads models |
| 🌐 Bilingual UI | Switch between Chinese and English at the top of the page. All 66 strings update immediately without refresh, restart, or losing uploaded audio |
| 🎤 Reference timbre library | The last timbre is pre-filled automatically; switch between multiple timbres in a dropdown and persist audio to `timbre_library/` |
| 🎚️ Mixing fixes | Preserve full-length stereo accompaniment, vocal start offset, accompaniment gain, and overall clipping protection |
| 🔧 Pure PyTorch SoX fallback | Works around the unavailable torchaudio SoX extension on Windows for echo/reverb effects |
| 🇨🇳 Mainland-China mirror pipeline (source install) | ModelScope for main weights + hf-mirror for runtime models + Tsinghua PyPI + Alibaba Cloud cu124 wheels |
| ⬇️ Two-stage model downloader | `download_models.py`: SHA256 verification, resumable downloads, `--check-only` validation, and idempotent skipping |
| ⚡ Consecutive conversion optimization | A single cached SVC model bundle, VRAM release before separation, and offline startup that skips per-repository Hugging Face checks |
| 🧹 Output and uninstall cleanup | Unique output names, separation results written to a fixed application directory, temporary directories removed, and outputs/timbres/caches cleaned on uninstall |

**Fork strategy**: this repository is based on upstream commit `5dc4796`. Enhancements are maintained as independent commits on top of it, rather than as a submodule or patch, so users with repository access can clone and run it directly or roll back individual changes. To synchronize upstream updates, add upstream as a remote and merge as needed.

---

## 🛠️ Source Installation (For Developers)

Most Windows users should use the Release installer above. The following instructions are for users who need to modify code or manage their own environment. The current Release provides only a Windows installer; Linux / macOS still require a source installation. Because the repository is private, cloning requires the appropriate GitHub permissions, and model downloads require network access to the Mainland-China or official sources described below.

### Windows

1. Install [Python 3.10](https://mirrors.huaweicloud.com/python/3.10.11/python-3.10.11-amd64.exe) and enable “Add to PATH”.
2. After cloning the repository, double-click **`setup_windows.bat`**. The script creates `.venv` → installs dependencies (including torch 2.4.0+cu124, about 2.5 GB) → adds the OpenMP runtime → deploys FFmpeg → downloads all models.
3. Double-click **`run_gradio.bat`**, then open <http://127.0.0.1:30911> in a browser.

```bat
git clone https://github.com/yonye1080/YingMusic-SVC-Launcher.git YingMusic-SVC
cd YingMusic-SVC
setup_windows.bat
```

### Linux / macOS

```bash
git clone https://github.com/yonye1080/YingMusic-SVC-Launcher.git YingMusic-SVC
cd YingMusic-SVC
bash setup.sh            # official sources by default; use "bash setup.sh cn" in Mainland China
```

> Python 3.10 is required (for example, `conda create -n ymsvc python=3.10`).
> The Linux script installs FFmpeg/SoX through apt; users of other distributions should use their own package manager.

---

## 🚀 Usage

### Web UI (Recommended)

- **Release installer / portable build**: use the Start Menu or desktop shortcut, or double-click **`start.bat`** in the program directory. This is the only launch entry point shipped in the distribution.
- **Source installation**: double-click **`run_gradio.bat`**, or run manually:

```bash
# Windows
.venv\Scripts\python.exe gradio_app.py
# Linux/macOS
.venv/bin/python gradio_app.py
```

By default, the server listens only on `127.0.0.1` (local machine access). If LAN sharing is genuinely needed, set `YINGMUSIC_SERVER_NAME=0.0.0.0` before launch. The UI exposes arbitrary weight paths and generated files, so enabling this on an untrusted network is not recommended.

Four tabs:

- **⚡ One-click Separation + Conversion**: upload a full song with accompaniment plus a reference timbre, and output lead vocals, harmony, accompaniment, converted vocals, and a mixed result in one run.
- **🎚️ Accompaniment Separation**: batch stem separation (corresponding to `run_separation.bat`).
- **🎤 Standalone Singing Voice Conversion**: change the timbre of an existing clean vocal, with optional accompaniment upload for automatic mixing.
- **🧩 Global Settings**: pre-filled weight paths and adjustable Diffusion Steps / FP16 / GPU ID.

> The command-line and batch scripts below are source-installation entry points. They are not included in the Release or portable builds; those distributions launch the Web UI only through `start.bat`.

### Command-Line Inference

Edit `SOURCE` / `TARGET` / `ACCOMPANY` / `VOCAL_OFFSET` / `INST_GAIN` in `run_infer.bat`, then double-click it. Results are written to `outputs\my_exp\`. Alternatively, call the script directly:

```bash
python my_inference.py --source src.wav --target timbre.wav \
  --checkpoint checkpoints/YingMusic-SVC-full.pt --config configs/YingMusic-SVC.yml \
  --diffusion-steps 100 --fp16 True --vocal-offset 0.0 --inst-gain -3.0
```

### Batch Accompaniment Separation

Place songs in `accom_separation\samples\raw\`, double-click `run_separation.bat`, and find results in `raw-infer\`.

---

## 📌 Practical Constraints (Important)

- **Reference audio is best at 5–10 seconds, with 6–8 seconds as the sweet spot**; 25 seconds is a hard limit in the code. Longer references produce shorter output chunks and slower inference.
- **8 GB VRAM**: keep FP16 enabled and Diffusion Steps at the default 100. If one-click mode runs out of VRAM, use the two-step flow: separate first, then run standalone SVC.
- **Zero-shot has no timbre registration**: every inference uses the reference audio for semantic, timbre, and F0 computation. The timbre library only avoids repeated uploads; it does not remove that computation.
- **One-click mode** derives accompaniment from automatic separation, so it is naturally aligned with the dry vocal (internal fixed offset 0 / -3 dB). Adjust the offset only when supplying your own accompaniment.
- **Result directories**: Web UI conversions go to `outputs\gradio\` (mixed audio in `accompany\`), separation results to `outputs\separated\<song name>\`, command-line results to `outputs\my_exp\`, and batch separation results to `accom_separation\samples\raw-infer\`. All directories live under the program directory, even when the app is launched from a shortcut with a different working directory.

---

## ⬇️ Models and Downloads

Model acquisition depends on the installation type:

- **Release installer / portable build**: all 6 model groups are bundled. `download_models.py` is not needed, and the application runs without internet access.
- **Source installation**: `setup_*.bat/.sh` calls `download_models.py` to download all 6 model groups. Once the models are in place, routine inference does not require internet access.

> `start.bat` in the portable build and installer sets `HF_HUB_OFFLINE=1` by default. Since all models are bundled, there is no need to contact Hugging Face for validation on every startup. Without internet access, each repository can otherwise retry for 30–60 seconds, delaying the first conversion by up to ten minutes. To temporarily fetch models online, run `set HF_HUB_OFFLINE=0` before launching.

### Download Sources: Mainland China / Overseas

> This section applies only to source installations and `download_models.py`. The Release installer already bundles the models and does not require choosing a download source.

The full pipeline (models + Python dependencies) supports two source sets:

| Stage | `cn` (Mainland China) | `official` (overseas) |
|---|---|---|
| 2 main weights | ModelScope | huggingface.co |
| 4 runtime models | hf-mirror.com | huggingface.co |
| Python dependencies | `requirements-cn.txt` (Tsinghua PyPI + Alibaba Cloud `cu124`) | `requirements-official.txt` (PyPI.org + `download.pytorch.org/whl/cu124`) |

The one-click scripts use platform-specific defaults, which can also be selected explicitly:

```bat
setup_windows.bat              :: Mainland-China sources (default)
setup_windows.bat official     :: official sources
```

```bash
./setup.sh          # official sources (default)
./setup.sh cn       # Mainland-China sources
```

**When installing dependencies manually, choose the file for your region** (package versions are defined only once in `requirements.txt`; the two files below only select sources):

```bash
pip install -r requirements-cn.txt         # Mainland China
pip install -r requirements-official.txt   # overseas
```

> Why the files are split: an `--index-url` inside a pip requirements file takes precedence over `-i` on the command line.
> Putting the source into the main requirements file would make `-i` ineffective and prevent region switching.
> Therefore, `requirements.txt` contains only the package list. Running `pip install -r requirements.txt` directly
> uses pip's default source, which may be slow in Mainland China.

### Model List

The Release already bundles all models below; source installations download them to the corresponding paths through `download_models.py`.

| Model | Local path | Size | License |
|---|---|---|---|
| YingMusic-SVC-full.pt | `checkpoints/` | 697.8 MiB | CC BY-NC 4.0 (non-commercial) |
| bs_roformer.ckpt | `accom_separation/ckpt/bs_roformer/` | 1.21 GiB | CC BY-NC 4.0 (non-commercial) |
| RMVPE | `checkpoints/` (HF cache) | 172.8 MiB | MIT + “research use only” clause |
| CAMPPlus | `checkpoints/` (HF cache) | 26.7 MiB | Apache-2.0 |
| BigVGAN v2 | `checkpoints/hf_cache/` | 466.4 MiB | MIT |
| Whisper small | `checkpoints/hf_cache/` | 922.2 MiB | Apache-2.0 |

For source installations or environment maintenance, models can be managed manually:

```bash
python download_models.py                   # download all missing models from Mainland-China mirrors (default)
python download_models.py --mirror official # official sources (overseas, or when direct HF access works)
python download_models.py --check-only      # validate only; exit code 1 if anything is missing
python download_models.py --only rmvpe      # process only the specified model
```

Models that are already present and pass verification are skipped automatically. Main weights support resumable downloads and strict SHA256 verification.
If one source is unavailable, the failure message includes the command for switching sources.

---

## 📦 Packaging and Release (For Maintainers)

Most users do not need this section. It is only for rebuilding the portable package or installer.

**Current release status**: `v1.0.0` has been published under Git tag [`v1.0.0`](https://github.com/yonye1080/YingMusic-SVC-Launcher/releases/tag/v1.0.0). The Release has 5 assets: `Setup.exe`, three `.bin` split archives, and `SHA256SUMS.txt`. The repository is currently private, so only authorized users can access it.

```bat
REM 1) Portable build (bundles embeddable Python, dependencies, weights, and FFmpeg)
build_portable.bat                       :: default D:\YingMusic-SVC-Portable
build_portable.bat D:\MyPortable         :: specify a target directory

REM 2) Installer (Inno Setup 6 must be installed first)
installer\build_installer.bat            :: default payload D:\YingMusic-SVC-Portable, output D:\YingMusic-SVC-Installer\out
installer\build_installer.bat <payload directory> <output directory>
```

- **Icon**: `installer/assets/icon-source.png` is the only source image. `installer/make_icon.py` removes the white background, center-crops it to a square, and scales it to seven sizes from 16–256 px to produce `installer/assets/app.ico`. To change the icon, replace the source image and rerun the script.
- **Chinese installer UI**: `installer/ChineseSimplified.isl` is a community-maintained Simplified Chinese translation for Inno Setup (based on 6.5.0+, UTF-8 with BOM), because official Inno Setup ships only a limited set of languages. The wizard first asks for a language, with Simplified Chinese as the default.
- **Install location**: `PrivilegesRequired=lowest` + `DefaultDirName={autopf}` resolves to `%LocalAppData%\Programs\YingMusic-SVC-Launcher`, requiring no administrator privileges. The app writes `outputs\`, `timbre_library\`, and `ui_lang.json` inside its own directory, which would fail for a normal user under `Program Files`.
- **Split output**: the payload is about 8.4 GiB, exceeding the 2 GB single-file limit, so `DiskSpanning` produces `Setup.exe` + `Setup-1/2/3.bin` (5.34 GB / 4.98 GiB total for v1.0.0). **The 4 installer files must always be published and distributed together in one directory**; a missing part makes installation impossible. `SHA256SUMS.txt` is included for download verification.
- **Size trimming**: `build_portable.bat` deletes `torch/lib/*.lib` (762 MiB of static import libraries) and `torch/include` (27 MiB of headers / 8,573 files). Both are needed only when compiling C++ extensions, not for inference. v1.0.0 installs about 8.15 GiB / 34,066 files. Since these files compress extremely well, the download size is reduced by only about 90 MiB; the main saving is disk space.
- **Only `start.bat` is shipped as an entry point**: `run_gradio.bat` / `run_infer.bat` / `run_separation.bat` point to `.venv\Scripts\python.exe`, while the portable and installer builds have no `.venv` (they use the bundled `python\`), so those scripts would exit immediately if double-clicked. `setup_windows.bat` / `setup.sh` / `setup_models.py` belong to the source-installation path, `my_infer.sh` is a Linux template, and `build_*.bat` are build-time scripts; all are excluded from the distribution. Source installations still use them.
- **Uninstall**: the prompt asking whether to delete `outputs` / `timbre_library` is placed in `usUninstall`, not `usPostUninstall`. `[UninstallDelete]` runs before the latter, which would otherwise leave an empty directory after an app had been used and then uninstalled. The numba cache written by `start.bat` to `%LocalAppData%\YingMusic-SVC-Launcher` is also removed during uninstall.
- The installer is not code-signed. On first launch, users see a SmartScreen “Unknown publisher” warning; after verifying the source and hashes, choose “More info → Run anyway”.
- v1.0.0 has been validated locally for installation, real conversion, and uninstallation, but has not yet been tested on a separate fully clean Windows machine.

---

## 📝 License (Read Carefully)

This repository and the Release installer involve **three different license categories**. Please comply with each separately. MIT covers the code only; bundling models into the installer does not automatically extend that license to the models:

- **Code: MIT** (see `LICENSE`, Copyright (c) 2025 Gongyu CHEN).
- **Main weights (`YingMusic-SVC-full.pt`, `bs_roformer.ckpt`): CC BY-NC 4.0, non-commercial use only.**
- **Third-party runtime models**: CAMPPlus / Whisper small are **Apache-2.0**, and BigVGAN v2 is **MIT**.
  RMVPE is MIT but ships with an upstream “for research use only” clause, so **it should not be treated as commercially usable**.
  See `NOTICE` for per-model sources and original terms.

> ⚠️ **The strictest term governs the combined use**: even though some third-party models use permissive licenses, running this repository requires the CC BY-NC 4.0 main weights. Therefore, **all outputs produced using this repository together with those weights are limited to non-commercial use**.
> Commercial use requires separate authorization from the main-weight rights holder (GiantAILab). See `NOTICE` for details.

---

## 🙏 Acknowledgments and Citation

This repository is based on [GiantAILab/YingMusic-SVC](https://github.com/GiantAILab/YingMusic-SVC), whose construction references [Seed-VC](https://github.com/Plachtaa/seed-vc). All model rights remain with their respective owners.

If you use YingMusic-SVC in research, please cite:

```bibtex
@article{chen2025yingmusicsvc,
  title={YingMusic-SVC: Real-World Robust Zero-Shot Singing Voice Conversion with Flow-GRPO and Singing-Specific Inductive Biases},
  author={Chen, Gongyu and Zhang, Xiaoyu and Weng, Zhenqiang and Zheng, Junjie and Shen, Da and Ding, Chaofan and Zhang, Wei-Qiang and Chen, Zihao},
  journal={arXiv preprint arXiv:2512.04793},
  year={2025}
}
```
