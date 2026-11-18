import os
import shutil
import tempfile
import json
import hashlib
from typing import Optional, Tuple
import gradio as gr


# ---------------- i18n ----------------
# UI language: "zh" (default) or "en". The choice is persisted to ui_lang.json
# so the next launch uses the same language. Set YMSVC_LANG=zh|en as a first-run
# default only; an explicit in-page choice always wins.
LANG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui_lang.json")
DEFAULT_LANG = "zh"
_LANG = None

# Every user-visible string lives here as (中文, English).
_TEXT = {
    "doc_title": (
        "YingMusic-SVC 歌声转换",
        "YingMusic-SVC: Real-World Robust Zero-Shot Singing Voice Conversion with Flow-GRPO and Singing-Specific Inductive Biases",
    ),
    "page_title": (
        "### YingMusic-SVC · 零样本歌声转换",
        "### YingMusic-SVC: Real-World Robust Zero-Shot Singing Voice Conversion with Flow-GRPO and Singing-Specific Inductive Biases",
    ),
    "lang_label": ("界面语言", "Language"),
    "lang_info": ("切换后立即生效，选择会自动保存", "Applies immediately; your choice is saved"),
    "lang_hint": (
        "切换语言不会清空已上传的音频；设置会记住，下次启动保持。也可用环境变量 `YMSVC_LANG=zh|en` 设置首次默认语言。",
        "Switching does not clear uploaded audio; the choice is saved for next launch. You can also set `YMSVC_LANG=zh|en` for the first-run default.",
    ),
    "tab_global": ("🧩 全局设置", "🧩 Global Settings"),
    "global_intro": (
        "这里设置共用参数，三种模式都会使用这些值。路径已预填好，一般不用改。",
        "Set shared parameters here. All three modes reuse these values.",
    ),
    "sep_group_title": ("**伴奏分离设置**", "**Separation Settings**"),
    "sep_cfg_label": ("分离配置（config_path）", "Separation Config (config_path)"),
    "sep_cfg_info": ("bs_roformer 的 YAML 配置文件路径", "Path to bs_roformer YAML config"),
    "sep_ckpt_label": ("分离权重（start_check_point）", "Separation Checkpoint (start_check_point)"),
    "sep_ckpt_info": ("bs_roformer 权重文件路径", "Path to bs_roformer ckpt"),
    "sep_device_label": ("分离 GPU（设备编号）", "Separation GPU (device id)"),
    "sep_device_info": ("默认填 0；仅 CPU 时会自动回退", "Use 0 for default; on CPU-only, it will fallback automatically"),
    "svc_group_title": ("**歌声转换设置**", "**SVC Settings**"),
    "svc_ckpt_label": ("SVC 主模型权重", "SVC Checkpoint"),
    "svc_ckpt_info": ("SVC .pt 权重文件路径", "Path to SVC .pt weights"),
    "svc_cfg_label": ("SVC 配置文件", "SVC Config"),
    "svc_cfg_info": (
        "YAML 配置路径（默认使用 configs/YingMusic-SVC.yml）",
        "YAML config path (defaults to configs/YingMusic-SVC.yml if present)",
    ),
    "svc_steps_label": ("扩散步数", "Diffusion Steps"),
    "svc_steps_info": ("越大越稳定但越慢；100 是较好的平衡", "Higher is steadier but slower; 100 is a good balance"),
    "svc_cuda_label": ("SVC GPU（cuda 编号）", "SVC GPU (cuda)"),
    "svc_cuda_info": ("多显卡时指定使用的 GPU 编号", "GPU index when multiple GPUs are available"),
    "svc_fp16_label": ("FP16 半精度", "FP16"),
    "svc_fp16_info": ("节省显存并加速推理；8 GB 显存建议开启", "Saves VRAM and speeds up inference on supported GPUs"),
    "tab_sep": ("🎚️ 伴奏分离", "🎚️ Accompaniment Separation"),
    "sep_intro": (
        "上传带伴奏的歌曲，分离出主唱、和声与纯伴奏。",
        "Upload an accompanied track to obtain Lead (vocals), Backing vocals, and pure Accompaniment.",
    ),
    "accompanied_audio": ("带伴奏的歌曲", "Accompanied Audio"),
    "btn_sep": ("开始分离", "Start Separation"),
    "out_lead": ("主唱", "Lead"),
    "out_back": ("和声", "Backing"),
    "out_acc": ("伴奏", "Accompaniment"),
    "tab_svc": ("🎤 独立歌声转换", "🎤 Standalone SVC"),
    "svc_intro": (
        "上传源干声与参考音色；可选上传伴奏，自动混音出成品。",
        "Upload source vocal and reference timbre (optionally upload accompaniment to auto-mix).",
    ),
    "src_vocal": ("源干声（主唱）", "Source Vocal (leading)"),
    "ref_timbre": ("参考音色", "Reference Timbre"),
    "timbre_lib": ("音色库", "Timbre library"),
    "timbre_lib_info": (
        "启动时会自动带出上次使用的音色；把音频放进 timbre_library\\ 或 prompts\\ 即可加入",
        "Last reference is restored on startup; add files to timbre_library\\ or prompts\\",
    ),
    "sample_timbre_1": ("使用示例音色 1", "Use Sample Timbre 1"),
    "sample_timbre_2": ("使用示例音色 2", "Use Sample Timbre 2"),
    "accompany_opt": ("伴奏（可选）", "Accompaniment (optional)"),
    "vocal_offset": ("人声起始偏移（秒）", "Vocal start offset (s)"),
    "vocal_offset_info": (
        "伴奏有前奏时填写前奏长度，让人声对齐；从原歌分离出的干声填 0",
        "Delay the vocal to line up with an accompaniment intro",
    ),
    "inst_gain": ("伴奏音量（dB）", "Accompaniment gain (dB)"),
    "inst_gain_info": ("0 为等响；负值让伴奏更轻、人声更突出", "0 = equal loudness; negative = quieter accompaniment"),
    "btn_convert": ("开始转换", "Convert"),
    "out_vc": ("转换后的人声", "Converted Vocal"),
    "out_mixed": ("混音成品（提供伴奏才有）", "Mixed with Accompaniment (if provided)"),
    "tab_all": ("⚡ 一键分离 + 转换", "⚡ One-Click Separation + SVC"),
    "all_intro": (
        "上传带伴奏歌曲和参考音色，一步完成分离与转换（最吃显存）。",
        "Upload accompanied audio and reference timbre, then run separation and conversion in one go.",
    ),
    "btn_all": ("一键处理", "Process All"),
    "oc_mixed": ("混音成品", "Mixed with Accompaniment"),
    "footer": ("— 祝你玩得开心 —", "— Enjoy —"),
    # runtime errors
    "err_no_mix": ("请先上传带伴奏的歌曲。", "Please upload an accompanied audio file."),
    "err_no_source": ("请先上传源干声。", "Please upload the source vocal."),
    "err_no_timbre": ("请先上传参考音色。", "Please upload the reference timbre."),
    "err_not_found": ("{name} 不存在：{path}", "{name} not found: {path}"),
    "err_no_stems": ("没有找到分离结果，请检查分离配置和权重路径。", "No stems found. Please check separation config and checkpoint."),
    "name_input_audio": ("输入音频", "Input audio"),
    "name_sep_config": ("分离配置", "Separation config"),
    "name_sep_ckpt": ("分离权重", "Separation checkpoint"),
    "name_source": ("源干声", "Source vocal"),
    "name_timbre": ("参考音色", "Reference timbre"),
    "name_svc_ckpt": ("SVC 主模型权重", "SVC checkpoint"),
    "name_svc_config": ("SVC 配置文件", "SVC config"),
    "name_accompany": ("伴奏文件", "Accompaniment file"),
}


def current_lang() -> str:
    """Resolve UI language: in-process choice > saved file > env default > zh."""
    global _LANG
    if _LANG in ("zh", "en"):
        return _LANG
    try:
        with open(LANG_FILE, "r", encoding="utf-8") as fh:
            saved = (json.load(fh).get("lang") or "").strip().lower()
        if saved in ("zh", "en"):
            _LANG = saved
            return _LANG
    except Exception:
        pass
    env = (os.environ.get("YMSVC_LANG") or "").strip().lower()
    _LANG = env if env in ("zh", "en") else DEFAULT_LANG
    return _LANG


def set_lang(lang: str) -> str:
    """Persist the chosen language and make it effective in this process."""
    global _LANG
    lang = (lang or "").strip().lower()
    if lang not in ("zh", "en"):
        lang = DEFAULT_LANG
    _LANG = lang
    try:
        with open(LANG_FILE, "w", encoding="utf-8") as fh:
            json.dump({"lang": lang}, fh, ensure_ascii=False)
    except Exception:
        pass
    return lang


def tr(key: str, lang: Optional[str] = None) -> str:
    return _TEXT[key][0 if (lang or current_lang()) == "zh" else 1]


# ---------------- Utilities ----------------
AUDIO_EXTS = (".wav", ".mp3", ".flac", ".ogg", ".m4a")
TIMBRE_DIR = os.path.join("timbre_library")
TIMBRE_STATE = os.path.join(TIMBRE_DIR, "last.json")


def _ensure_file_exists(path: str, name: str):
    if not path or not os.path.isfile(path):
        raise gr.Error(tr("err_not_found").format(name=name, path=path))


def _timbre_library_choices():
    """Reusable reference audios: personal library first, then bundled prompts."""
    items, seen = [], set()
    for folder in (TIMBRE_DIR, "prompts"):
        if not os.path.isdir(folder):
            continue
        for fname in sorted(os.listdir(folder)):
            if not fname.lower().endswith(AUDIO_EXTS):
                continue
            path = os.path.join(folder, fname)
            label = fname if folder == TIMBRE_DIR else f"{fname} (sample)"
            if label in seen:
                continue
            seen.add(label)
            items.append((label, path))
    return items


def _last_timbre():
    """Reference audio used in the previous session, if the file still exists."""
    try:
        with open(TIMBRE_STATE, "r", encoding="utf-8") as fh:
            path = json.load(fh).get("path", "")
        return path if path and os.path.isfile(path) else None
    except Exception:
        return None


def _remember_timbre(path: str):
    """Persist a copy of the reference audio so the next launch can preload it."""
    if not path or not os.path.isfile(path):
        return
    os.makedirs(TIMBRE_DIR, exist_ok=True)
    abs_path = os.path.abspath(path)
    persistent_roots = [os.path.abspath(TIMBRE_DIR), os.path.abspath("prompts")]
    if os.path.dirname(abs_path) in persistent_roots:
        saved = abs_path
    else:
        stem, ext = os.path.splitext(os.path.basename(path))
        with open(abs_path, "rb") as fh:
            digest = hashlib.sha256(fh.read(1 << 20)).hexdigest()[:8]
        safe_stem = "".join(c for c in stem if c.isalnum() or c in "-_")[:24] or "timbre"
        saved = os.path.join(TIMBRE_DIR, f"{safe_stem}_{digest}{ext}")
        if not os.path.isfile(saved):
            shutil.copy2(abs_path, saved)
    with open(TIMBRE_STATE, "w", encoding="utf-8") as fh:
        json.dump({"path": os.path.abspath(saved)}, fh, ensure_ascii=False)


def _maybe_default_bs_roformer_paths() -> Tuple[str, str]:
    cfg = os.path.join("accom_separation", "ckpt", "bs_roformer", "config_bd_roformer.yaml")
    ckpt = os.path.join("accom_separation", "ckpt", "bs_roformer", "bs_roformer.ckpt")
    return (cfg if os.path.isfile(cfg) else "", ckpt if os.path.isfile(ckpt) else "")


def _default_svc_cfg() -> str:
    candidate = os.path.join("configs", "YingMusic-SVC.yml")
    return candidate if os.path.isfile(candidate) else ""


def _locate_stem(out_dir: str, name_candidates: Tuple[str, ...]) -> Optional[str]:
    for stem in name_candidates:
        wav_path = os.path.join(out_dir, f"{stem}.wav")
        flac_path = os.path.join(out_dir, f"{stem}.flac")
        if os.path.isfile(wav_path):
            return wav_path
        if os.path.isfile(flac_path):
            return flac_path
    return None


# ---------------- Separation ----------------
def run_separation(
    mix_file: str,
    sep_config_path: str,
    sep_checkpoint_path: str,
    sep_device_id: int,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Return (lead, backing, accompany)
    """
    if not mix_file:
        raise gr.Error(tr("err_no_mix"))
    _ensure_file_exists(mix_file, tr("name_input_audio"))
    _ensure_file_exists(sep_config_path, tr("name_sep_config"))
    _ensure_file_exists(sep_checkpoint_path, tr("name_sep_ckpt"))

    input_dir = tempfile.mkdtemp(prefix="ams_in_")
    output_dir = tempfile.mkdtemp(prefix="ams_out_")
    mix_basename = os.path.basename(mix_file)
    mix_copy_path = os.path.join(input_dir, mix_basename)
    shutil.copy2(mix_file, mix_copy_path)

    from accom_separation.inference import proc_folder

    args = {
        "model_type": "bs_roformer",
        "config_path": sep_config_path,
        "start_check_point": sep_checkpoint_path,
        "input_folder": input_dir,
        "store_dir": output_dir,
        "extract_instrumental": True,
        "extract_other": False,
        "device_ids": [int(sep_device_id)],
        "disable_detailed_pbar": True,
        "force_cpu": False,
        "flac_file": False,
        "use_tta": False,
    }
    proc_folder(args)

    song_name = os.path.splitext(mix_basename)[0]
    song_out_dir = os.path.join(output_dir, song_name)

    lead = _locate_stem(song_out_dir, ("vocals", "lead", "leading_vocals"))
    backing = _locate_stem(song_out_dir, ("backing_vocal", "backing", "back_vocals", "background"))
    accompany = _locate_stem(song_out_dir, ("instrumental", "accompaniment"))

    if not any([lead, backing, accompany]):
        raise gr.Error(tr("err_no_stems"))
    return lead, backing, accompany


# ---------------- SVC ----------------
def run_svc(
    source_vocal: str,
    target_timbre: str,
    accompany_file: Optional[str],
    svc_checkpoint: str,
    svc_config: str,
    svc_steps: int,
    svc_cuda_index: int,
    svc_fp16: bool,
    vocal_offset_sec: float = 0.0,
    instrument_gain_db: float = -3.0,
) -> Tuple[str, Optional[str]]:
    """
    Return (converted vocal, mixed with accompaniment when provided)
    """
    if not source_vocal:
        raise gr.Error(tr("err_no_source"))
    if not target_timbre:
        raise gr.Error(tr("err_no_timbre"))
    _ensure_file_exists(source_vocal, tr("name_source"))
    _ensure_file_exists(target_timbre, tr("name_timbre"))
    _ensure_file_exists(svc_checkpoint, tr("name_svc_ckpt"))
    _ensure_file_exists(svc_config, tr("name_svc_config"))
    if accompany_file:
        _ensure_file_exists(accompany_file, tr("name_accompany"))

    try:
        _remember_timbre(target_timbre)
    except Exception:
        pass

    import types
    import torch
    from Remix.auger import echo_then_reverb_save
    from my_inference import load_models_api, run_inference

    args = types.SimpleNamespace()
    args.source = source_vocal
    args.target = target_timbre
    args.diffusion_steps = int(svc_steps)
    args.checkpoint = svc_checkpoint
    args.expname = "gradio"
    args.cuda = torch.device(f"cuda:{int(svc_cuda_index)}") if torch.cuda.is_available() else torch.device("cpu")
    args.fp16 = bool(svc_fp16)
    args.accompany = accompany_file if accompany_file else None
    args.config = svc_config
    args.length_adjust = 1.0
    args.inference_cfg_rate = 0.7
    args.f0_condition = True
    args.semi_tone_shift = None
    args.output = "./outputs"
    os.makedirs(args.output, exist_ok=True)

    model_bundle = load_models_api(args, device=args.cuda)
    vc_path = run_inference(args, model_bundle, device=args.cuda)

    mixed_out = None
    if accompany_file:
        base_dir = os.path.dirname(vc_path)
        fname = os.path.basename(vc_path)
        acc_dir = os.path.join(base_dir, "accompany")
        os.makedirs(acc_dir, exist_ok=True)
        mixed_out = os.path.join(acc_dir, fname)
        try:
            offset = float(vocal_offset_sec) if vocal_offset_sec is not None else 0.0
        except (TypeError, ValueError):
            offset = 0.0
        try:
            gain = float(instrument_gain_db) if instrument_gain_db is not None else -3.0
        except (TypeError, ValueError):
            gain = -3.0
        echo_then_reverb_save(
            vc_path, mixed_out, accompany_file,
            vocal_offset_sec=offset,
            instrument_gain_db=gain,
        )
    return vc_path, mixed_out


# ---------------- One-click Pipeline ----------------
def run_pipeline(
    mix_file: str,
    target_timbre: str,
    # separation settings
    sep_config_path: str,
    sep_checkpoint_path: str,
    sep_device_id: int,
    # svc settings
    svc_checkpoint: str,
    svc_config: str,
    svc_steps: int,
    svc_cuda_index: int,
    svc_fp16: bool,
) -> Tuple[Optional[str], Optional[str], Optional[str], str, Optional[str]]:
    lead, backing, accompany = run_separation(
        mix_file=mix_file,
        sep_config_path=sep_config_path,
        sep_checkpoint_path=sep_checkpoint_path,
        sep_device_id=sep_device_id,
    )
    vc_path, mixed_out = run_svc(
        source_vocal=lead or "",
        target_timbre=target_timbre,
        accompany_file=accompany,
        svc_checkpoint=svc_checkpoint,
        svc_config=svc_config,
        svc_steps=svc_steps,
        svc_cuda_index=svc_cuda_index,
        svc_fp16=svc_fp16,
        vocal_offset_sec=0.0,
        instrument_gain_db=-3.0,
    )
    return lead, backing, accompany, vc_path, mixed_out


# ---------------- UI ----------------
def build_ui(lang: Optional[str] = None):
    lang = lang or current_lang()
    T = lambda k: tr(k, lang)

    default_sep_cfg, default_sep_ckpt = _maybe_default_bs_roformer_paths()
    default_svc_cfg = _default_svc_cfg()
    default_svc_ckpt = os.path.join("checkpoints", "YingMusic-SVC-full.pt")
    if not os.path.isfile(default_svc_ckpt):
        default_svc_ckpt = ""
    header_img = os.path.join("figs", "svc_main.jpg")
    has_header_img = os.path.isfile(header_img)

    # discover sample timbres
    prompt_dir = "prompts"
    audio_exts = (".wav", ".mp3", ".flac", ".ogg", ".m4a")
    sample_timbres = []
    if os.path.isdir(prompt_dir):
        for fname in sorted(os.listdir(prompt_dir)):
            if fname.lower().endswith(audio_exts):
                sample_timbres.append(os.path.join(prompt_dir, fname))
            if len(sample_timbres) >= 2:
                break

    timbre_choices = _timbre_library_choices()
    last_timbre_path = _last_timbre()
    last_timbre_choice = None
    if last_timbre_path:
        abs_last = os.path.abspath(last_timbre_path)
        for _label, _path in timbre_choices:
            if os.path.abspath(_path) == abs_last:
                last_timbre_choice = _path
                break

    # Registry of translatable components: (component, {prop: text_key}).
    # Both the change-event outputs and its payload are derived from this list,
    # so they can never get out of sync.
    lang_registry = []

    def _reg(comp, **keys):
        lang_registry.append((comp, keys))
        return comp

    with gr.Blocks(
        title=T("doc_title"),
        theme=gr.themes.Soft(),
    ) as demo:
        with gr.Row():
            with gr.Column(scale=1):
                _reg(gr.Markdown(T("page_title")), value="page_title")
            if has_header_img:
                with gr.Column(scale=1):
                    gr.Image(header_img, show_label=False, height=140)

        with gr.Row():
            with gr.Column(scale=1):
                lang_radio = _reg(
                    gr.Radio(
                        choices=[("中文", "zh"), ("English", "en")],
                        value=lang,
                        label=T("lang_label"),
                        info=T("lang_info"),
                    ),
                    label="lang_label",
                    info="lang_info",
                )
            with gr.Column(scale=2):
                _reg(gr.Markdown(T("lang_hint")), value="lang_hint")

        with gr.Tab(T("tab_global")) as tab_global:
            _reg(tab_global, label="tab_global")
            _reg(gr.Markdown(T("global_intro")), value="global_intro")
            with gr.Group():
                _reg(gr.Markdown(T("sep_group_title")), value="sep_group_title")
                sep_cfg_inp = _reg(
                    gr.Textbox(value=default_sep_cfg, label=T("sep_cfg_label"), info=T("sep_cfg_info")),
                    label="sep_cfg_label", info="sep_cfg_info",
                )
                sep_ckpt_inp = _reg(
                    gr.Textbox(value=default_sep_ckpt, label=T("sep_ckpt_label"), info=T("sep_ckpt_info")),
                    label="sep_ckpt_label", info="sep_ckpt_info",
                )
                sep_device_inp = _reg(
                    gr.Number(value=0, label=T("sep_device_label"), precision=0, info=T("sep_device_info")),
                    label="sep_device_label", info="sep_device_info",
                )
            with gr.Group():
                _reg(gr.Markdown(T("svc_group_title")), value="svc_group_title")
                svc_ckpt_inp = _reg(
                    gr.Textbox(value=default_svc_ckpt, label=T("svc_ckpt_label"), info=T("svc_ckpt_info")),
                    label="svc_ckpt_label", info="svc_ckpt_info",
                )
                svc_cfg_inp = _reg(
                    gr.Textbox(value=default_svc_cfg, label=T("svc_cfg_label"), info=T("svc_cfg_info")),
                    label="svc_cfg_label", info="svc_cfg_info",
                )
                svc_steps_inp = _reg(
                    gr.Number(value=100, label=T("svc_steps_label"), precision=0, info=T("svc_steps_info")),
                    label="svc_steps_label", info="svc_steps_info",
                )
                svc_cuda_inp = _reg(
                    gr.Number(value=0, label=T("svc_cuda_label"), precision=0, info=T("svc_cuda_info")),
                    label="svc_cuda_label", info="svc_cuda_info",
                )
                svc_fp16_inp = _reg(
                    gr.Checkbox(value=True, label=T("svc_fp16_label"), info=T("svc_fp16_info")),
                    label="svc_fp16_label", info="svc_fp16_info",
                )

        with gr.Tab(T("tab_sep")) as tab_sep:
            _reg(tab_sep, label="tab_sep")
            _reg(gr.Markdown(T("sep_intro")), value="sep_intro")
            with gr.Row():
                with gr.Column(scale=1):
                    mix_file = _reg(
                        gr.Audio(label=T("accompanied_audio"), type="filepath"),
                        label="accompanied_audio",
                    )
                    # example if available
                    example_path = os.path.join("accom_separation", "samples", "raw", "All I Want For Christmas Is You01.MP3")
                    if os.path.isfile(example_path):
                        gr.Examples(
                            examples=[[example_path]],
                            inputs=[mix_file],
                            label="示例音频 / Examples",
                        )
                    btn_sep = _reg(gr.Button(T("btn_sep"), variant="primary"), value="btn_sep")
                with gr.Column(scale=1):
                    out_lead = _reg(gr.Audio(label=T("out_lead"), type="filepath"), label="out_lead")
                    out_back = _reg(gr.Audio(label=T("out_back"), type="filepath"), label="out_back")
                    out_acc = _reg(gr.Audio(label=T("out_acc"), type="filepath"), label="out_acc")
            btn_sep.click(
                fn=run_separation,
                inputs=[mix_file, sep_cfg_inp, sep_ckpt_inp, sep_device_inp],
                outputs=[out_lead, out_back, out_acc],
            )

        with gr.Tab(T("tab_svc")) as tab_svc:
            _reg(tab_svc, label="tab_svc")
            _reg(gr.Markdown(T("svc_intro")), value="svc_intro")
            with gr.Row():
                with gr.Column(scale=1):
                    with gr.Row():
                        src_vocal = _reg(
                            gr.Audio(label=T("src_vocal"), type="filepath"),
                            label="src_vocal",
                        )
                        ref_timbre = _reg(
                            gr.Audio(label=T("ref_timbre"), type="filepath", value=last_timbre_path),
                            label="ref_timbre",
                        )
                    timbre_picker = _reg(
                        gr.Dropdown(
                            choices=timbre_choices,
                            value=last_timbre_choice,
                            label=T("timbre_lib"),
                            info=T("timbre_lib_info"),
                        ),
                        label="timbre_lib", info="timbre_lib_info",
                    )
                    # sample timbre buttons
                    if len(sample_timbres) >= 1:
                        btn_t1 = _reg(gr.Button(T("sample_timbre_1")), value="sample_timbre_1")
                    if len(sample_timbres) >= 2:
                        btn_t2 = _reg(gr.Button(T("sample_timbre_2")), value="sample_timbre_2")
                    accompany_opt = _reg(
                        gr.Audio(label=T("accompany_opt"), type="filepath"),
                        label="accompany_opt",
                    )
                    with gr.Row():
                        vocal_offset_inp = _reg(
                            gr.Number(
                                value=0.0,
                                label=T("vocal_offset"),
                                info=T("vocal_offset_info"),
                            ),
                            label="vocal_offset", info="vocal_offset_info",
                        )
                        inst_gain_inp = _reg(
                            gr.Number(
                                value=-3.0,
                                label=T("inst_gain"),
                                info=T("inst_gain_info"),
                            ),
                            label="inst_gain", info="inst_gain_info",
                        )
                    btn_svc = _reg(gr.Button(T("btn_convert"), variant="primary"), value="btn_convert")
                with gr.Column(scale=1):
                    out_vc = _reg(gr.Audio(label=T("out_vc"), type="filepath"), label="out_vc")
                    out_mixed = _reg(gr.Audio(label=T("out_mixed"), type="filepath"), label="out_mixed")

            # wire sample buttons for SVC
            def _sample_1():
                return sample_timbres[0] if len(sample_timbres) >= 1 else None

            def _sample_2():
                return sample_timbres[1] if len(sample_timbres) >= 2 else None

            timbre_picker.change(fn=lambda p: p, inputs=[timbre_picker], outputs=[ref_timbre])
            if len(sample_timbres) >= 1:
                btn_t1.click(fn=_sample_1, inputs=[], outputs=[ref_timbre])
            if len(sample_timbres) >= 2:
                btn_t2.click(fn=_sample_2, inputs=[], outputs=[ref_timbre])

            btn_svc.click(
                fn=run_svc,
                inputs=[
                    src_vocal,
                    ref_timbre,
                    accompany_opt,
                    svc_ckpt_inp,
                    svc_cfg_inp,
                    svc_steps_inp,
                    svc_cuda_inp,
                    svc_fp16_inp,
                    vocal_offset_inp,
                    inst_gain_inp,
                ],
                outputs=[out_vc, out_mixed],
            )

        with gr.Tab(T("tab_all")) as tab_all:
            _reg(tab_all, label="tab_all")
            _reg(gr.Markdown(T("all_intro")), value="all_intro")
            with gr.Row():
                with gr.Column(scale=1):
                    with gr.Row():
                        mix_in = _reg(
                            gr.Audio(label=T("accompanied_audio"), type="filepath"),
                            label="accompanied_audio",
                        )
                        ref_in = _reg(
                            gr.Audio(label=T("ref_timbre"), type="filepath", value=last_timbre_path),
                            label="ref_timbre",
                        )
                    timbre_picker_all = _reg(
                        gr.Dropdown(
                            choices=timbre_choices,
                            value=last_timbre_choice,
                            label=T("timbre_lib"),
                            info=T("timbre_lib_info"),
                        ),
                        label="timbre_lib", info="timbre_lib_info",
                    )
                    # example if available
                    example_path2 = os.path.join("accom_separation", "samples", "raw", "All I Want For Christmas Is You01.MP3")
                    if os.path.isfile(example_path2):
                        gr.Examples(
                            examples=[[example_path2]],
                            inputs=[mix_in],
                            label="示例音频 / Examples",
                        )
                    # sample timbre buttons for pipeline
                    if len(sample_timbres) >= 1:
                        btn_pt1 = _reg(gr.Button(T("sample_timbre_1")), value="sample_timbre_1")
                    if len(sample_timbres) >= 2:
                        btn_pt2 = _reg(gr.Button(T("sample_timbre_2")), value="sample_timbre_2")
                    btn_all = _reg(gr.Button(T("btn_all"), variant="primary"), value="btn_all")
                with gr.Column(scale=1):
                    oc_lead = _reg(gr.Audio(label=T("out_lead"), type="filepath"), label="out_lead")
                    oc_back = _reg(gr.Audio(label=T("out_back"), type="filepath"), label="out_back")
                    oc_acc = _reg(gr.Audio(label=T("out_acc"), type="filepath"), label="out_acc")
                    oc_vc = _reg(gr.Audio(label=T("out_vc"), type="filepath"), label="out_vc")
                    oc_mixed = _reg(gr.Audio(label=T("oc_mixed"), type="filepath"), label="oc_mixed")

            # wire sample buttons for pipeline
            timbre_picker_all.change(fn=lambda p: p, inputs=[timbre_picker_all], outputs=[ref_in])
            if len(sample_timbres) >= 1:
                btn_pt1.click(fn=_sample_1, inputs=[], outputs=[ref_in])
            if len(sample_timbres) >= 2:
                btn_pt2.click(fn=_sample_2, inputs=[], outputs=[ref_in])

            btn_all.click(
                fn=run_pipeline,
                inputs=[
                    mix_in,
                    ref_in,
                    sep_cfg_inp,
                    sep_ckpt_inp,
                    sep_device_inp,
                    svc_ckpt_inp,
                    svc_cfg_inp,
                    svc_steps_inp,
                    svc_cuda_inp,
                    svc_fp16_inp,
                ],
                outputs=[oc_lead, oc_back, oc_acc, oc_vc, oc_mixed],
            )

        _reg(gr.Markdown(T("footer")), value="footer")

        # ---- language switch ----
        def _lang_payload(new_lang, *extra):
            # Gradio versions differ on whether a js callback's return value
            # replaces or appends to the Python inputs, so accept either shape.
            candidates = [new_lang, *extra]
            for v in list(candidates):
                if isinstance(v, (list, tuple)):
                    candidates.extend(v)
            code = next(
                (v.strip().lower() for v in candidates
                 if isinstance(v, str) and v.strip().lower() in ("zh", "en")),
                "zh",
            )
            set_lang(code)
            U = lambda k: tr(k, code)
            return [
                gr.update(**{prop: U(key) for prop, key in keys.items()})
                for _comp, keys in lang_registry
            ]

        # JS fallback: force tab labels / document title to update even if the
        # frontend does not re-render tabitem props from a server update.
        js_data = json.dumps(
            {
                "tabs": {
                    code: [tr(k, code) for k in ("tab_global", "tab_sep", "tab_svc", "tab_all")]
                    for code in ("zh", "en")
                },
                "title": {code: tr("doc_title", code) for code in ("zh", "en")},
            },
            ensure_ascii=False,
        )
        switch_js = (
            "(lang) => { try { const D = " + js_data + "; "
            "const L = D.tabs[lang] || D.tabs.zh; "
            "const tabs = document.querySelectorAll('[role=\"tab\"]'); "
            "for (let i = 0; i < Math.min(4, tabs.length); i++) { tabs[i].textContent = L[i]; } "
            "if (D.title[lang]) { document.title = D.title[lang]; } "
            "} catch (e) { console.warn('i18n switch:', e); } return [lang]; }"
        )
        lang_radio.change(
            fn=_lang_payload,
            inputs=[lang_radio],
            outputs=[comp for comp, _keys in lang_registry],
            js=switch_js,
        )

        return demo


if __name__ == "__main__":
    app = build_ui()
    app.launch(server_port=30911, inbrowser=True, server_name='0.0.0.0')
