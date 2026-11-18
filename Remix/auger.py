import torch
import torchaudio
try:
    from torchaudio import sox_effects
except (ImportError, RuntimeError):  # torchaudio SoX extension is unavailable on Windows
    sox_effects = None
from typing import List, Optional, Tuple
import librosa
import numpy as np
import math
import torch.nn.functional as F
import soundfile as sf
from pathlib import Path

def ensure_2d(wave):
    """确保音频是 [C, T] 格式"""
    if wave.dim() == 1:
        wave = wave.unsqueeze(0)  # [T] -> [1, T]
    return wave

def safe_normalize(wave, peak=0.98):
    """安全归一化，防止削波"""
    max_val = wave.abs().max()
    if max_val > peak:
        wave = wave * (peak / max_val)
    return wave

def align_length(processed_wave, target_length):
    """
    对齐音频长度
    Args:
        processed_wave: 处理后的音频张量 [C, T]
        target_length: 目标长度
    Returns:
        长度对齐后的音频张量
    """
    current_length = processed_wave.shape[1]
    if current_length > target_length:
        return processed_wave[:, :target_length]  # 截断
    elif current_length < target_length:
        padding = target_length - current_length
        return torch.nn.functional.pad(processed_wave, (0, padding))  # 填充零
    else:
        return processed_wave

EFFECT_PARAMS = {
    # Echo 参数 (SoX格式)
    'echo': {
        'delay_ms': 110.0,  # 延迟时间(毫秒)
        'feedback': 0.2,  # 反馈强度 (0-1)
        'wet': 0.18,  # 混合比例 (0-1)
    },

    # Reverb 参数 (SoX格式)
    'reverb': {
        'reverberance': 55,  # 混响强度 (0-100)
        'hf_damping': 65,  # 高频阻尼 (0-100)
        'room_scale': 65,  # 房间大小 (0-100)
        'stereo_depth': 100,  # 立体声深度 (0-100)
        'pre_delay_ms': 25,  # 预延迟(毫秒)
        'wet': 0.25,  # 混合比例 (0-1)
    },

}

@torch.no_grad()
def _torch_echo(w: torch.Tensor, sr: int, parts: list) -> torch.Tensor:
    """SoX `echo` 的纯 PyTorch 近似（Windows 无 SoX 扩展时的回退实现）。"""
    delay_ms = float(parts[3]) if len(parts) > 3 else 110.0
    decay = float(parts[4]) if len(parts) > 4 else 0.3
    delay = max(1, int(round(delay_ms / 1000.0 * sr)))
    out = w.clone()
    for k in range(1, 5):
        d = delay * k
        if d >= w.shape[1]:
            break
        shifted = torch.zeros_like(w)
        shifted[:, d:] = w[:, :-d]
        out = out + (decay ** k) * shifted
    return out


@torch.no_grad()
def _torch_reverb(w: torch.Tensor, sr: int, parts: list) -> torch.Tensor:
    """SoX `reverb` 的纯 PyTorch 近似：多抽头延迟 + 低通高频阻尼。"""
    reverberance = float(parts[1]) / 100.0 if len(parts) > 1 else 0.5
    pre_delay_ms = float(parts[5]) if len(parts) > 5 else 25.0
    pre = max(0, int(round(pre_delay_ms / 1000.0 * sr)))
    taps = [(19, 0.55), (37, 0.40), (53, 0.30), (71, 0.22), (97, 0.15)]
    out = w.clone()
    for ms, gain in taps:
        d = pre + int(round(ms / 1000.0 * sr))
        if d >= w.shape[1]:
            continue
        shifted = torch.zeros_like(w)
        shifted[:, d:] = w[:, :-d]
        out = out + reverberance * gain * shifted
    damped = torchaudio.functional.lowpass_biquad(out, sr, cutoff_freq=6000)
    return 0.6 * out + 0.4 * damped


@torch.no_grad()
def _fallback_effect(w: torch.Tensor, sr: int, eff) -> torch.Tensor:
    parts = eff[0] if eff else []
    name = str(parts[0]).lower() if parts else ""
    if name == "echo":
        return _torch_echo(w, sr, parts)
    if name == "reverb":
        return _torch_reverb(w, sr, parts)
    return w


@torch.no_grad()
def _apply_sox_effects_cpu(wave: torch.Tensor, sr: int, eff):
    """
    确保 SoX 在 CPU/float32 上跑，并把结果搬回 wave 的 device/dtype。
    Windows 上 torchaudio 不带 SoX 扩展，自动切换到纯 PyTorch 实现。
    wave: [T] 或 [C,T]
    eff:  SoX effects 列表
    """
    wave2d = ensure_2d(wave)
    ref_device, ref_dtype = wave2d.device, wave2d.dtype
    w_cpu = wave2d.to("cpu", dtype=torch.float32, non_blocking=False).contiguous()
    try:
        if sox_effects is None:
            raise RuntimeError("torchaudio SoX extension unavailable")
        y_cpu, _ = sox_effects.apply_effects_tensor(w_cpu, sr, eff)  # SoX 要求 CPU,float32
    except (RuntimeError, OSError, AttributeError):
        y_cpu = _fallback_effect(w_cpu, sr, eff)
    y = y_cpu.to(device=ref_device, dtype=ref_dtype)
    return y

def apply_echo(wave, sr, delay_ms=150.0, feedback=0.4, wet=0.35):
    wave = ensure_2d(wave)
    original_length = wave.shape[1]
    try:
        eff = [["echo", "0.8", "0.9", str(int(delay_ms)), str(feedback)]]
        y = _apply_sox_effects_cpu(wave, sr, eff)
    except RuntimeError as e:
        print(f"Echo参数错误，使用简化版本: {e}")
        eff = [["echo", "0.8", "0.9", str(int(delay_ms)), "0.3"]]
        y = _apply_sox_effects_cpu(wave, sr, eff)
    y = align_length(y, original_length)
    y = (1 - wet) * wave + wet * y
    return safe_normalize(y)



def apply_reverb(wave, sr, reverberance=80, hf_damping=40, room_scale=120,
                stereo_depth=100, pre_delay_ms=25, wet=0.5):
    wave = ensure_2d(wave)
    original_length = wave.shape[1]
    try:
        eff = [["reverb", str(reverberance), str(hf_damping), str(room_scale),
               str(stereo_depth), str(pre_delay_ms)]]
        y = _apply_sox_effects_cpu(wave, sr, eff)
    except RuntimeError:
        try:
            eff = [["reverb", str(reverberance), str(hf_damping), str(room_scale)]]
            y = _apply_sox_effects_cpu(wave, sr, eff)
        except RuntimeError:
            try:
                eff = [["reverb", str(reverberance)]]
                y = _apply_sox_effects_cpu(wave, sr, eff)
            except RuntimeError:
                print("所有reverb参数格式都失败，使用默认参数")
                eff = [["reverb"]]
                y = _apply_sox_effects_cpu(wave, sr, eff)
    y = align_length(y, original_length)
    y = (1 - wet) * wave + wet * y
    return safe_normalize(y)

@torch.no_grad()
def echo_then_reverb_save(
    audio_path: str,
    out_path: str,
    instrument_path: str | None = None,
    echo_kwargs: dict | None = None,
    reverb_kwargs: dict | None = None,
    target_sr: int | None = None,
    peak: float = 0.98,
    vocal_offset_sec: float = 0.0,
    instrument_gain_db: float = -3.0,
):
    """
    读取人声 -> 回声 -> 混响 -> 与伴奏混合后保存。
    - vocal_offset_sec: 人声延后多少秒进入，用于对齐带前奏的伴奏
    - instrument_gain_db: 伴奏相对人声的增益(dB)，负值 = 伴奏更轻
    - 保留伴奏全长与立体声；输出长度取两者最大值，不再按短边截断
    """
    audio_path = Path(audio_path)
    # 1) 读取
    wave, sr = torchaudio.load(str(audio_path))  # [C, T]
    wave = wave.to(torch.float32)
    # 统一到 [-1,1]
    if wave.abs().max() > 1.0:
        wave = wave / (wave.abs().max() + 1e-12)

    # 2) 采样率处理（可选）
    out_sr = sr if target_sr is None else int(target_sr)
    if out_sr != sr:
        resampler = torchaudio.transforms.Resample(sr, out_sr)
        wave = resampler(wave)
        sr = out_sr

    # 3) 效果参数合并
    ep = dict(EFFECT_PARAMS)
    if echo_kwargs:
        ep["echo"] = {**ep.get("echo", {}), **echo_kwargs}
    if reverb_kwargs:
        ep["reverb"] = {**ep.get("reverb", {}), **reverb_kwargs}

    y = wave
    # 4) 先回声 -> 再混响
    y = apply_echo(
        y, sr,
        delay_ms=ep["echo"]["delay_ms"],
        feedback=ep["echo"]["feedback"],
        wet=ep["echo"]["wet"]
    )
    y = apply_reverb(
        y, sr,
        reverberance=ep["reverb"]["reverberance"],
        hf_damping=ep["reverb"]["hf_damping"],
        room_scale=ep["reverb"]["room_scale"],
        stereo_depth=ep["reverb"]["stereo_depth"],
        pre_delay_ms=ep["reverb"]["pre_delay_ms"],
        wet=ep["reverb"]["wet"]
    )
    y = safe_normalize(y, peak=peak)

    # 5) 人声转单声道；效果处理本就在单声道上完成
    vocal = y.cpu().numpy().mean(axis=0).astype(np.float32)

    # 无伴奏时只保存加了效果的人声，避免 librosa.load(None) 报错
    if instrument_path is None:
        sf.write(out_path, vocal, sr)
        return str(out_path)

    # 6) 伴奏：保留声道数，重采样到与人声一致
    inst, _ = librosa.load(instrument_path, sr=sr, mono=False)
    inst = np.asarray(inst, dtype=np.float32)
    if inst.ndim == 1:
        inst = inst[None, :]  # [1, T]

    # 7) 响度：人声 -2 dBFS；伴奏 -2 dBFS + 用户增益
    #    伴奏按整体峰值归一化，保持左右声道原有平衡
    vocal = amplify_to_peak(vocal, target_db=-2)
    inst_peak = float(np.max(np.abs(inst)))
    if inst_peak > 1e-9:
        inst = inst * (10 ** (-2 / 20.0) / inst_peak)
    inst = inst * (10 ** (float(instrument_gain_db) / 20.0))

    # 8) 人声延后 shift 秒进入；总长取最大值，伴奏完整保留
    shift = max(0, int(round(float(vocal_offset_sec) * sr)))
    total = max(len(vocal) + shift, inst.shape[1])
    mix = np.zeros((inst.shape[0], total), dtype=np.float32)
    mix[:, :inst.shape[1]] += inst
    mix[:, shift:shift + len(vocal)] += vocal[None, :]

    # 9) 整体防削波，保持人声/伴奏的相对比例
    mix_peak = float(np.max(np.abs(mix)))
    if mix_peak > peak:
        mix = mix * (peak / mix_peak)
    mix = np.clip(mix, -1.0, 1.0)

    sf.write(out_path, mix.T, sr)  # [T, C]，立体声伴奏 -> 立体声输出
    return str(out_path)

def amplify_to_peak(wav: np.ndarray, target_db: float = -2.0) -> np.ndarray:
    """
    把音频整体放大/缩小到目标峰值 (例如 -2 dBFS)
    wav: numpy array from librosa.load
    target_db: 目标峰值 (默认 -2 dB)
    """
    target_amp = 10 ** (target_db / 20.0)   # -2 dBFS ≈ 0.794
    peak = np.max(np.abs(wav))
    if peak < 1e-9:
        return wav  # 全静音，不处理
    gain = target_amp / peak
    return wav * gain

