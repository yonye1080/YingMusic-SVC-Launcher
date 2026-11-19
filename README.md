# YingMusic-SVC · 增强分发版

**简体中文** | [English](README.en.md)

> 基于 [GiantAILab/YingMusic-SVC](https://github.com/GiantAILab/YingMusic-SVC) 的增强 fork：
> **Windows 一键安装 + 完整离线运行 + 中英双语界面 + 参考音色库 + 混音修复 + 国内镜像全链路**。
> 源码仓库不直接存放模型权重；Windows Release 安装包已内置全部模型，源码安装则由脚本自动下载。

**YingMusic-SVC** 是一个真实场景鲁棒的零样本歌声转换（Zero-Shot SVC）框架，融合连续预训练、
鲁棒监督微调与 Flow-GRPO 强化学习，在带伴奏、和声干扰等真实歌曲条件下仍能保持稳定的
音色相似度与可懂度。论文：[arXiv:2512.04793](https://arxiv.org/abs/2512.04793)。

---

## 📥 下载与安装（普通用户）

**当前版本：[v1.0.0](https://github.com/yonye1080/YingMusic-SVC-Launcher/releases/tag/v1.0.0)**（已发布，非草稿）。

> 当前 GitHub 仓库为**私有**，Release 仅对有仓库权限的用户可见；若要面向公众分发，需要另行调整仓库可见性。Release 共包含 4 个安装文件和 1 个 `SHA256SUMS.txt`。

Windows 安装包已内置 Python、依赖、FFmpeg 和全部模型，**安装后无需再下载模型，运行无需联网**。

1. 从 Release 下载以下 **4 个文件**，并放在同一个文件夹：
   - `YingMusic-SVC-Launcher-1.0.0-Setup.exe`
   - `YingMusic-SVC-Launcher-1.0.0-Setup-1.bin`
   - `YingMusic-SVC-Launcher-1.0.0-Setup-2.bin`
   - `YingMusic-SVC-Launcher-1.0.0-Setup-3.bin`
2. 运行 `Setup.exe`，按向导完成安装，无需管理员权限。缺少任何一个 `.bin` 都无法安装。
3. 从开始菜单或桌面快捷方式启动，浏览器打开 <http://127.0.0.1:30911>。

| 项目 | 当前版本实测 |
|---|---|
| 下载量 | **5.34 GB / 4.98 GiB** |
| 安装后占用 | **约 8.15 GiB** |
| 默认安装位置 | `%LocalAppData%\Programs\YingMusic-SVC-Launcher` |
| 系统 | Windows 10 / 11 64 位 |
| 显卡 | 推荐 NVIDIA；驱动建议 r550 或更新（支持 CUDA 12.4） |

Release 同时提供 `SHA256SUMS.txt`，可用于校验四个安装文件的完整性。安装包暂未做代码签名，首次运行若出现 SmartScreen「未知发布者」，请确认文件来源与哈希后，选择「更多信息 → 仍要运行」。

**当前验证状态**：已在 Windows + RTX 4060 8GB 环境完成全新静默安装、安装目录实际音频转换、从非程序工作目录启动、连续转换、重复分轨及完整卸载；目录、快捷方式与缓存均无残留。尚未在另一台完全干净、未装过开发环境的 Windows 机器上做最终验证。

---

## ✨ 本版增强（相对上游）

| 增强 | 说明 |
|---|---|
| 🪟 Windows 一键安装 | Release 提供完整离线安装包；源码可用 `setup_windows.bat` 一键配置环境、部署 FFmpeg 并下载模型 |
| 🌐 中英双语界面 | 页面顶部切换，66 条文案即时生效，不刷新、不重启、不丢已上传音频 |
| 🎤 参考音色库 | 上次音色自动预填，多音色下拉切换，音频持久化到 `timbre_library/` |
| 🎚️ 混音修复 | 伴奏保留全长与立体声、人声起始偏移、伴奏增益、整体防削波 |
| 🔧 SoX 纯 PyTorch 回退 | 解决 torchaudio SoX 扩展在 Windows 不可用的问题（回声/混响） |
| 🇨🇳 国内镜像全链路（源码安装） | ModelScope 主权重 + hf-mirror 运行时模型 + 清华 PyPI + 阿里云 cu124 wheel |
| ⬇️ 两段式模型下载 | `download_models.py`：SHA256 校验 + 断点续传 + `--check-only` 校验 + 幂等跳过 |
| ⚡ 连续转换优化 | 单份 SVC 模型缓存、分离前释放显存、离线跳过 Hugging Face 逐仓库校验 |
| 🧹 输出与卸载收尾 | 转换结果唯一命名，分轨结果固定写入程序目录并清理临时目录，卸载清理输出/音色库/缓存 |

**fork 策略**：本仓库基于上游 commit `5dc4796`，增强以独立提交叠加维护（非 submodule/patch），
有仓库权限后可直接 clone 即用，也可按需回退到上游。如需同步上游更新，将上游设为 remote 后 merge 即可。

---

## 🛠️ 源码安装（开发者）

普通 Windows 用户建议使用上方的 Release 安装包；以下方式适用于需要修改代码或自行管理环境的用户。当前 Release 仅提供 Windows 安装版，Linux / macOS 仍需源码安装；仓库为私有，克隆需要相应 GitHub 权限，模型下载则按下方国内 / 官方源配置网络。

### Windows

1. 安装 [Python 3.10](https://mirrors.huaweicloud.com/python/3.10.11/python-3.10.11-amd64.exe)（勾选 Add to PATH）。
2. 克隆本仓库后，双击 **`setup_windows.bat`**。脚本会依次：创建 `.venv` → 安装依赖
   （含 torch 2.4.0+cu124，约 2.5GB）→ 补位 OpenMP → 部署 FFmpeg → 下载全部模型。
3. 完成后双击 **`run_gradio.bat`**，浏览器打开 <http://127.0.0.1:30911>。

```bat
git clone https://github.com/yonye1080/YingMusic-SVC-Launcher.git YingMusic-SVC
cd YingMusic-SVC
setup_windows.bat
```

### Linux / macOS

```bash
git clone https://github.com/yonye1080/YingMusic-SVC-Launcher.git YingMusic-SVC
cd YingMusic-SVC
bash setup.sh            # 默认官方源；国内用 bash setup.sh cn
```

> 需要 Python 3.10（可用 `conda create -n ymsvc python=3.10`）。
> Linux 脚本会通过 apt 安装 ffmpeg/sox；其他发行版请用各自包管理器。

---

## 🚀 使用

### Web UI（推荐）

- **Release 安装版 / 便携版**：使用开始菜单或桌面快捷方式，也可以双击程序目录里的 **`start.bat`**。这是发行包唯一的启动入口。
- **源码安装**：双击 **`run_gradio.bat`**，或手动运行：

```bash
# Windows
.venv\Scripts\python.exe gradio_app.py
# Linux/macOS
.venv/bin/python gradio_app.py
```

默认只监听 `127.0.0.1`（本机可访问）。确实需要局域网共享时，启动前设置
`YINGMUSIC_SERVER_NAME=0.0.0.0`；界面会暴露任意权重路径和生成文件，不建议在不可信网络下开启。

四个标签页：

- **⚡ 一键分离 + 转换**：上传整首带伴奏歌曲 + 参考音色，一次输出主唱/和声/伴奏/转换人声/混音成品。
- **🎚️ 伴奏分离**：批量分轨（对应 `run_separation.bat`）。
- **🎤 独立歌声转换**：已有干净干声时换音色，可选上传伴奏自动混音。
- **🧩 全局设置**：权重路径已预填，Diffusion Steps / FP16 / GPU 编号可调。

> 以下命令行与批量脚本属于源码安装入口，Release / 便携包中不包含这些脚本；发行包只通过 `start.bat` 启动 Web UI。

### 命令行推理

编辑 `run_infer.bat` 中的 `SOURCE` / `TARGET` / `ACCOMPANY` / `VOCAL_OFFSET` / `INST_GAIN` 后双击，
结果在 `outputs\my_exp\`。或直接调用：

```bash
python my_inference.py --source src.wav --target timbre.wav \
  --checkpoint checkpoints/YingMusic-SVC-full.pt --config configs/YingMusic-SVC.yml \
  --diffusion-steps 100 --fp16 True --vocal-offset 0.0 --inst-gain -3.0
```

### 批量伴奏分轨

把歌曲放入 `accom_separation\samples\raw\`，双击 `run_separation.bat`，结果在 `raw-infer\`。

---

## 📌 实操约束（重要）

- **参考音频 5–10 秒最佳，甜点 6–8 秒**；25 秒为代码硬上限。参考越长，每分块产出越短、推理越慢。
- **8GB 显存**：保持 FP16 勾选、Diffusion Steps 默认 100；一键模式显存不足时改「先分轨、再独立 SVC」两步走。
- **zero-shot 无音色注册**：每次推理都会用参考音频参与语义/音色/F0 计算，音色库只省去「重复上传」，省不掉计算。
- **一键模式**的伴奏来自自动分离、与干声天然对齐（内部固定偏移 0 / -3 dB）；只有「自带伴奏」才需调偏移。
- **结果目录**：Web UI 转换结果 `outputs\gradio\`（混音在 `accompany\`）、分轨结果 `outputs\separated\<歌名>\`、命令行 `outputs\my_exp\`、批量分轨 `accom_separation\samples\raw-infer\`。目录都在程序自己所在的位置，从快捷方式启动也一样。

---

## ⬇️ 模型与下载

模型获取方式按安装类型区分：

- **Release 安装版 / 便携版**：6 类模型已全部随包，不需要调用 `download_models.py`，运行过程无需联网。
- **源码安装**：`setup_*.bat/.sh` 会调用 `download_models.py` 下载全部 6 类模型；模型就位后，日常推理无需联网。

> 便携版 / 安装包的 `start.bat` 默认设置 `HF_HUB_OFFLINE=1`：模型全部随包，没必要每次启动都去 Hugging Face 校验一遍（网络不通时每个仓库可能重试 30–60 秒，第一次转换会被拖到十分钟）。确实要临时联网取模型，启动前 `set HF_HUB_OFFLINE=0` 即可。

### 下载源：国内 / 海外都可切换

> 本节只适用于源码安装和 `download_models.py`；Release 安装包已内置模型，不需要选择下载源。

全链路（模型 + Python 依赖）支持两套源，按所在地区选择：

| 环节 | `cn`（国内） | `official`（海外） |
|---|---|---|
| 2 个主权重 | ModelScope | huggingface.co |
| 4 个运行时模型 | hf-mirror.com | huggingface.co |
| Python 依赖 | `requirements-cn.txt`（清华 PyPI + 阿里云 `cu124`） | `requirements-official.txt`（PyPI.org + `download.pytorch.org/whl/cu124`） |

一键脚本的默认值按平台设定，也可显式指定：

```bat
setup_windows.bat              :: 国内源（默认）
setup_windows.bat official     :: 海外源
```

```bash
./setup.sh          # 海外源（默认）
./setup.sh cn       # 国内源
```

**手动装依赖时按地区选文件**（包版本只在 `requirements.txt` 里定义一次，这两个文件仅负责选源）：

```bash
pip install -r requirements-cn.txt         # 国内
pip install -r requirements-official.txt   # 海外
```

> 为什么拆文件：pip 中**文件内的 `--index-url` 优先级高于命令行的 `-i`**，
> 把源写进主清单会导致 `-i` 完全失效、无法按地区切换。
> `requirements.txt` 因此只保留包列表；若直接 `pip install -r requirements.txt`，
> 会使用 pip 的默认源（国内可能较慢）。

### 模型清单

Release 已内置下列全部模型；源码安装会通过 `download_models.py` 下载到对应位置。

| 模型 | 本地路径 | 大小 | 许可 |
|---|---|---|---|
| YingMusic-SVC-full.pt | `checkpoints/` | 697.8 MiB | CC BY-NC 4.0（非商业） |
| bs_roformer.ckpt | `accom_separation/ckpt/bs_roformer/` | 1.21 GiB | CC BY-NC 4.0（非商业） |
| RMVPE | `checkpoints/`（HF cache） | 172.8 MiB | MIT + 「仅供研究使用」条款 |
| CAMPPlus | `checkpoints/`（HF cache） | 26.7 MiB | Apache-2.0 |
| BigVGAN v2 | `checkpoints/hf_cache/` | 466.4 MiB | MIT |
| Whisper small | `checkpoints/hf_cache/` | 922.2 MiB | Apache-2.0 |

源码安装或维护环境时，可手动管理模型：

```bash
python download_models.py                   # 国内镜像下载全部缺失模型（默认）
python download_models.py --mirror official # 官方源（海外 / 国内直连 HF 可行时）
python download_models.py --check-only      # 只校验不下载（有缺失时退出码为 1）
python download_models.py --only rmvpe      # 只处理指定模型
```

已就位且校验通过的模型会自动跳过；主权重支持断点续传与 SHA256 强校验。
某一路源不通时，脚本会在失败信息里直接提示换源命令。

---

## 📦 打包发行（维护者）

普通用户不需要本节；只有需要重新产出绿色版 / 安装包时才用。

**当前发布状态**：`v1.0.0` 已发布，对应 Git 标签 [`v1.0.0`](https://github.com/yonye1080/YingMusic-SVC-Launcher/releases/tag/v1.0.0)。Release 共 5 个资产：`Setup.exe`、3 个 `.bin` 分卷与 `SHA256SUMS.txt`；仓库当前为私有，仅授权用户可访问。

```bat
REM 1) 绿色免安装版（内置 embeddable Python、依赖、权重、ffmpeg）
build_portable.bat                       :: 默认 D:\YingMusic-SVC-Portable
build_portable.bat D:\MyPortable         :: 指定目标目录

REM 2) 安装包（Inno Setup 6，需先装好 Inno Setup）
installer\build_installer.bat            :: 默认 载荷 D:\YingMusic-SVC-Portable、输出 D:\YingMusic-SVC-Installer\out
installer\build_installer.bat <载荷目录> <输出目录>
```

- **图标**：`installer/assets/icon-source.png` 是唯一的源图；`installer/make_icon.py` 会抠掉白底、居中裁方，再压成 16–256 px 的 7 个尺寸，产出 `installer/assets/app.ico`。换图标只替换源图后重跑该脚本即可。
- **中文界面**：`installer/ChineseSimplified.isl` 是社区维护的 Inno Setup 简体中文翻译（基于 6.5.0+，UTF-8 带 BOM），因为 Inno Setup 官方只随附少数语种。安装向导会先弹语言选择，简体中文为默认。
- **装到哪**：`PrivilegesRequired=lowest` + `DefaultDirName={autopf}` ⇒ 影子目录 `%LocalAppData%\Programs\YingMusic-SVC-Launcher`，全程无需管理员权限。这样做是因为程序要往自己目录里写 `outputs\`、`timbre_library\`、`ui_lang.json`，装在 `Program Files` 下普通用户会写失败。
- **产物是分卷的**：载荷约 8.4 GiB，超过单文件 2 GB 上限，因此开启 `DiskSpanning`，产出 `Setup.exe` + `Setup-1/2/3.bin`（v1.0.0 合计 5.34 GB / 4.98 GiB）。**发布与分发时必须把 4 个安装文件整组放在同一目录**，缺一片就装不完；另附 `SHA256SUMS.txt` 供下载校验。
- **体积裁剪**：`build_portable.bat` 会删掉 `torch/lib/*.lib`（762 MiB 静态导入库）和 `torch/include`（27 MiB 头文件 / 8,573 个文件）——两者只在编译 C++ 扩展时用，推理不需要。v1.0.0 实测装完约 8.15 GiB / 34,066 个文件；因为这两块本身压缩率极高，下载量只少约 90 MiB，省的主要是磁盘。
- **包里只有 `start.bat` 一个入口**：`run_gradio.bat` / `run_infer.bat` / `run_separation.bat` 都指向 `.venv\Scripts\python.exe`，而便携包与安装包里没有 `.venv`（跑的是内置 `python\`），双击只会闪退；`setup_windows.bat` / `setup.sh` / `setup_models.py` 是源码安装链路，`my_infer.sh` 是 Linux 模板，`build_*.bat` 是构建期脚本，这些在打包时一并排除。源码安装照旧使用它们。
- **卸载**：询问「是否删除 outputs / timbre_library」这一步放在 `usUninstall` 而不是 `usPostUninstall`（`[UninstallDelete]` 早于后者执行，会导致装完跑过应用再卸载时留下一个空目录）；`start.bat` 的 numba 缓存写在 `%LocalAppData%\YingMusic-SVC-Launcher`，也在卸载时一并清掉。
- 安装包未做代码签名，用户首次运行会看到 SmartScreen「未知发布者」提示，确认文件来源与哈希后选「更多信息 → 仍要运行」即可。
- v1.0.0 已在本机完成安装、实际转换与卸载验证，但尚未在另一台完全干净的 Windows 机器上实测。

---

## 📝 许可证（务必阅读）

本仓库及 Release 安装包涉及**三类不同许可**，请分别遵守。MIT 只覆盖代码，不因为模型被打进安装包而自动覆盖模型：

- **代码：MIT**（见 `LICENSE`，Copyright (c) 2025 Gongyu CHEN）。
- **主权重（`YingMusic-SVC-full.pt`、`bs_roformer.ckpt`）：CC BY-NC 4.0，仅限非商业。**
- **第三方运行时模型**：CAMPPlus / Whisper small 为 **Apache-2.0**，BigVGAN v2 为 **MIT**；
  RMVPE 为 MIT，但上游随附「本软件仅供研究使用」条款，**不建议视为可商用**。
  逐项来源与原文见 `NOTICE`。

> ⚠️ **整体用途受最严格项约束**：即使部分第三方模型属宽松许可，运行本仓库必须使用
> CC BY-NC 4.0 的主权重，因此**基于本仓库 + 上述权重运行所得的全部输出，仅限非商业用途**。
> 商用须另行取得主权重权利方（GiantAILab）授权。详见 `NOTICE`。

---

## 🙏 致谢与引用

本仓库基于 [GiantAILab/YingMusic-SVC](https://github.com/GiantAILab/YingMusic-SVC)，
其构建参考了 [Seed-VC](https://github.com/Plachtaa/seed-vc)。全部模型权利归原权利人。

如在研究中使用 YingMusic-SVC，请引用：

```bibtex
@article{chen2025yingmusicsvc,
  title={YingMusic-SVC: Real-World Robust Zero-Shot Singing Voice Conversion with Flow-GRPO and Singing-Specific Inductive Biases},
  author={Chen, Gongyu and Zhang, Xiaoyu and Weng, Zhenqiang and Zheng, Junjie and Shen, Da and Ding, Chaofan and Zhang, Wei-Qiang and Chen, Zihao},
  journal={arXiv preprint arXiv:2512.04793},
  year={2025}
}
```
