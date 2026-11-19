"""YingMusic-SVC 模型下载 / 校验脚本（两段式，覆盖全部 6 类模型）。

本脚本是 setup_models.py 的超集：除原有的 4 类运行时模型外，还把 2 个主权重
纳入脚本化下载。首次安装依赖后运行一次即可把全部模型就位，运行过程无需联网。

  - 主权重（2 个，仅限非商业）：走 ModelScope / HuggingFace 直链，
    流式下载 + 断点续传 + SHA256 强校验，落到代码期望的精确路径。
  - 运行时模型（4 类）：复用 HF cache 布局，两处缓存根与 setup_models.py
    完全一致（rmvpe/campplus -> checkpoints/，bigvgan/whisper -> checkpoints/hf_cache/）。

用法：
  python download_models.py                   # 国内镜像下载全部缺失模型（默认）
  python download_models.py --mirror official # 改用官方源（海外 / 国内直连 HF 可行时）
  python download_models.py --check-only      # 只校验不下载；有缺失时退出码为 1
  python download_models.py --only yingmusic_svc_full bs_roformer  # 只处理指定模型

下载源（--mirror）：
  cn        主权重走 ModelScope，运行时模型走 hf-mirror.com（国内推荐）
  official  主权重走 huggingface.co，运行时模型走 huggingface.co（海外推荐）
            该模式会清除外部残留的 HF_ENDPOINT，确保真正直连官方站点。

模型清单见 configs/model_paths.yaml。脚本可重复运行，已就位且校验通过的模型自动跳过。
"""
import argparse
import hashlib
import os
import sys
import time
from pathlib import Path

import yaml  # pyyaml，requirements.txt 已包含

ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "configs" / "model_paths.yaml"
CKPT = ROOT / "checkpoints"
HF_CACHE = CKPT / "hf_cache"
CACHE_MAP = {"ckpt": CKPT, "hf_cache": HF_CACHE}
CN_ENDPOINT = "https://hf-mirror.com"
CHUNK = 1 << 20  # 1 MiB


def human(n):
    return f"{n / 1073741824:.2f} GiB" if n >= 1073741824 else f"{n / 1048576:.1f} MiB"


def sha256_of(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------- 主权重（直链）
def check_direct(m):
    p = ROOT / m["path"]
    if not p.exists():
        return False, "缺失：" + m["path"]
    size = p.stat().st_size
    if size != m["bytes"]:
        return False, f"大小不符：{m['path']}（{size} != {m['bytes']}）"
    if sha256_of(p) != m["sha256"]:
        return False, "SHA256 不符：" + m["path"]
    return True, f"已就位（{human(size)}，sha256 匹配）"


def download_direct(m, mirror, timeout=60):
    dest = ROOT / m["path"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + ".part")
    expected = m["bytes"]

    if part.exists() and part.stat().st_size > expected:
        print("  .part 比预期体积更大，已丢弃重下")
        part.unlink()

    if part.exists() and part.stat().st_size == expected:
        # A previous run finished the transfer but died before the checksum, so
        # the .part is complete. Re-requesting it with Range would return 416
        # and strand the download forever; verify it instead.
        print("  发现完整的 .part（上次中断在校验前），直接校验")
    else:
        if not _download_to_part(m, mirror, part, timeout):
            return False

    if part.stat().st_size != expected:
        print(f"  大小不符（{part.stat().st_size} != {expected}），保留 .part 可重试续传")
        return False
    if sha256_of(part) != m["sha256"]:
        print("  SHA256 不符，已删除损坏文件")
        part.unlink()
        return False
    part.replace(dest)
    print(f"  完成 -> {m['path']}（sha256 校验通过）")
    return True


def _download_to_part(m, mirror, part, timeout=60):
    """Stream into .part with resume support. Returns True when the transfer ends."""
    import requests  # huggingface-hub 的依赖，安装依赖后必已存在

    url = m["url"][mirror]
    headers, mode, resume = {}, "wb", 0
    if part.exists() and part.stat().st_size > 0:
        resume = part.stat().st_size
        headers["Range"] = f"bytes={resume}-"
        mode = "ab"
    print("  下载 " + url)
    if resume:
        print(f"  断点续传：从 {human(resume)} 继续")
    try:
        with requests.get(url, stream=True, headers=headers,
                          timeout=timeout, allow_redirects=True) as r:
            if resume and r.status_code == 416:
                # 远端和 .part 大小对不上，续传无解：丢掉 .part 完整重下一次。
                r.close()
                part.unlink(missing_ok=True)
                print("  续传被拒（416），改为完整下载")
                return _download_to_part(m, mirror, part, timeout)
            if resume and r.status_code == 200:  # 服务器忽略 Range，重新下
                mode, resume = "wb", 0
            r.raise_for_status()
            total = int(r.headers.get("Content-Length", 0)) + resume
            done, t0 = resume, time.time()
            with part.open(mode) as f:
                for chunk in r.iter_content(chunk_size=CHUNK):
                    if chunk:
                        f.write(chunk)
                        done += len(chunk)
                        pct = done * 100 // total if total else 0
                        speed = (done - resume) / max(time.time() - t0, 1e-6)
                        print(f"\r  {human(done)}/{human(total)} ({pct}%) "
                              f"{human(int(speed))}/s", end="", flush=True)
        print()
        return True
    except Exception as e:  # noqa: BLE001
        print(f"\n  下载失败：{type(e).__name__}: {e}")
        print(f"  可手动下载后放入 {m['path']}")
        if m.get("manual"):
            print(f"  页面：{m['manual']}")
        print(f"  可换源重试：--mirror {'official' if mirror == 'cn' else 'cn'}")
        return False


# ---------------------------------------------------------------- 运行时模型（HF 缓存）
def hf_setup_env(mirror):
    # 须在 import huggingface_hub 之前设置 HF_ENDPOINT 才会生效。
    if mirror == "cn":
        # setdefault：尊重用户自己已配置的镜像（如公司内网镜像）
        os.environ.setdefault("HF_ENDPOINT", CN_ENDPOINT)
    else:
        # official 模式必须真正回到 huggingface.co：清除外部残留的 HF_ENDPOINT，
        # 否则若 shell 里曾 export HF_ENDPOINT=hf-mirror.com，--mirror official 会失效。
        os.environ.pop("HF_ENDPOINT", None)
    os.environ["HF_HOME"] = str(CKPT)
    os.environ["HF_HUB_CACHE"] = str(HF_CACHE)
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"


def check_hf(m):
    # 用 huggingface_hub 定位缓存文件（snapshot hash 可变，不写死路径），不联网。
    from huggingface_hub import try_to_load_from_cache

    cache_dir = str(CACHE_MAP[m["cache"]])
    path = try_to_load_from_cache(repo_id=m["repo_id"],
                                  filename=m["check_file"], cache_dir=cache_dir)
    if not path:
        return False, f"未缓存（{m['repo_id']} / {m['check_file']}）"
    p = Path(path)
    if not p.exists():
        return False, "缓存记录存在但文件缺失"
    size = p.stat().st_size
    if size != m["bytes"]:
        return False, f"大小不符（{size} != {m['bytes']}）"
    return True, f"已就位（{human(size)}）"


def download_hf(m, mirror="cn"):
    from huggingface_hub import hf_hub_download, snapshot_download

    cache_dir = str(CACHE_MAP[m["cache"]])
    try:
        if m["kind"] == "hf_file":
            path = hf_hub_download(repo_id=m["repo_id"],
                                   filename=m["filename"], cache_dir=cache_dir)
        else:
            path = snapshot_download(repo_id=m["repo_id"], cache_dir=cache_dir,
                                     allow_patterns=m["allow_patterns"])
        print("  OK -> " + str(path))
        return True
    except Exception as e:  # noqa: BLE001
        print(f"  失败：{type(e).__name__}: {e}")
        print("  可稍后重试（HF 缓存支持断点续传），或检查网络 / 镜像设置")
        print(f"  可换源重试：--mirror {'official' if mirror == 'cn' else 'cn'}")
        return False


# ---------------------------------------------------------------- 主流程
def main():
    ap = argparse.ArgumentParser(description="YingMusic-SVC 模型下载 / 校验")
    ap.add_argument("--mirror", choices=["cn", "official"], default="cn",
                    help="下载源，默认国内镜像 cn")
    ap.add_argument("--check-only", action="store_true",
                    help="只校验不下载；有缺失时退出码为 1")
    ap.add_argument("--only", nargs="*", metavar="ID",
                    help="只处理指定模型 id（见 configs/model_paths.yaml）")
    args = ap.parse_args()

    models = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))["models"]
    known_ids = [m["id"] for m in models]
    if args.only is not None:
        if not args.only:
            ap.error("--only 至少需要一个模型 id")
        unknown = [i for i in args.only if i not in known_ids]
        if unknown:
            ap.error("未知模型 id: " + ", ".join(unknown) + "\n可用 id: " + ", ".join(known_ids))
        wanted = set(args.only)
        models = [m for m in models if m["id"] in wanted]

    # 涉及 HF 模型时先配好环境（定位缓存 / 下载都需要；须在 import 前）
    if any(m["kind"] in ("hf_file", "hf_snapshot") for m in models):
        hf_setup_env(args.mirror)

    print(f"mirror={args.mirror}  check_only={args.check_only}")
    results = {}
    for m in models:
        print(f"\n>>> [{m['id']}] {m.get('desc', '')}")
        checker = check_direct if m["kind"] == "direct" else check_hf
        ok, msg = checker(m)
        print("  " + msg)
        if ok or args.check_only:
            results[m["id"]] = ok
            continue
        results[m["id"]] = (download_direct(m, args.mirror)
                            if m["kind"] == "direct" else download_hf(m, args.mirror))

    print("\n=== summary ===")
    for m in models:
        print(f"  {'OK ' if results[m['id']] else 'BAD'} {m['id']}")
    bad = [m["id"] for m in models if not results[m["id"]]]
    if bad:
        print(f"\n{len(bad)} 个模型未就绪：{', '.join(bad)}")
        other = "official" if args.mirror == "cn" else "cn"
        print(f"提示：可换源重试（当前 {args.mirror}）-> python download_models.py --mirror {other}")
        sys.exit(1)
    print("校验通过：全部模型已就位。" if args.check_only else "全部模型已就绪。")


if __name__ == "__main__":
    main()
