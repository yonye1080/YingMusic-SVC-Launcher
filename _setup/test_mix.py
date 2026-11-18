import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

import numpy as np
import soundfile as sf
from Remix.auger import echo_then_reverb_save

SR = 44100
t_v = np.arange(SR * 2) / SR
vocal = (0.5 * np.sin(2 * np.pi * 440 * t_v)).astype(np.float32)
t_i = np.arange(SR * 5) / SR
left = (0.6 * np.sin(2 * np.pi * 220 * t_i)).astype(np.float32)
right = (0.6 * np.sin(2 * np.pi * 330 * t_i)).astype(np.float32)
inst = np.stack([left, right], axis=1)

tmp = ROOT / "_setup" / "_mix_test"
tmp.mkdir(parents=True, exist_ok=True)
vp = tmp / "vocal.wav"
ip = tmp / "inst.wav"
sf.write(vp, vocal, SR)
sf.write(ip, inst, SR)


def tone_amp(seg, freq):
    n = len(seg)
    k = int(round(freq * n / SR))
    return float(abs(np.fft.rfft(seg)[k]) / n)


op = tmp / "mix.wav"
echo_then_reverb_save(str(vp), str(op), str(ip))
info = sf.info(op)
x, out_sr = sf.read(op)
peak = float(np.max(np.abs(x)))
print(f"[1] full-length stereo: duration={info.duration:.2f}s channels={info.channels} sr={out_sr} peak={peak:.3f}")
assert abs(info.duration - 5.0) < 0.02, "accompaniment was truncated"
assert info.channels == 2, "stereo was lost"
assert peak <= 0.981, "output still clips"

op2 = tmp / "mix_offset.wav"
echo_then_reverb_save(str(vp), str(op2), str(ip), vocal_offset_sec=1.0)
x2, _ = sf.read(op2)
head_440 = tone_amp(x2[: SR // 2, 0], 440)
mid_440 = tone_amp(x2[int(1.2 * SR):int(1.7 * SR), 0], 440)
print(f"[2] vocal offset 1.0s: duration={len(x2)/out_sr:.2f}s 440Hz head={head_440:.5f} after={mid_440:.5f}")
assert abs(len(x2) / out_sr - 5.0) < 0.02
assert mid_440 > head_440 * 3, "vocal offset was not applied"

op3 = tmp / "mix_gain.wav"
echo_then_reverb_save(str(vp), str(op3), str(ip), instrument_gain_db=-12.0)
x3, _ = sf.read(op3)
tail_default = float(np.sqrt(np.mean(x[int(4 * SR):, 0] ** 2)))
tail_quiet = float(np.sqrt(np.mean(x3[int(4 * SR):, 0] ** 2)))
print(f"[3] gain -12dB: accompaniment-only tail RMS {tail_quiet:.4f} vs default {tail_default:.4f}")
assert tail_quiet < tail_default * 0.95, "instrument gain was not applied"

op4 = tmp / "dry.wav"
echo_then_reverb_save(str(vp), str(op4))
i4 = sf.info(op4)
print(f"[4] no accompaniment: duration={i4.duration:.2f}s channels={i4.channels}")
assert abs(i4.duration - 2.0) < 0.02

ipm = tmp / "inst_mono.wav"
sf.write(ipm, left, SR)
op5 = tmp / "mix_mono.wav"
echo_then_reverb_save(str(vp), str(op5), str(ipm))
print(f"[5] mono accompaniment output channels: {sf.info(op5).channels}")
assert sf.info(op5).channels == 1

for p in tmp.iterdir():
    p.unlink()
tmp.rmdir()
print("ALL MIX TESTS PASSED")
