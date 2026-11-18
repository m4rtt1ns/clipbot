import subprocess
import numpy as np

SR = 16000


def audio_db(path):
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                       capture_output=True)
    x = np.frombuffer(p.stdout, dtype=np.int16).astype(np.float32) / 32768.0
    n = len(x) // SR
    if n < 60:
        return np.array([])
    x = x[: n * SR].reshape(n, SR)
    return 20 * np.log10(np.sqrt((x ** 2).mean(axis=1)) + 1e-6)


def smooth(v, k):
    return np.convolve(v, np.ones(k) / k, mode="same")


def robust_z(v, win=180, floor=1.0):
    out = np.zeros(len(v))
    for i in range(len(v)):
        seg = v[max(0, i - win): min(len(v), i + win)]
        med = np.median(seg)
        mad = np.median(np.abs(seg - med)) * 1.4826 + floor
        out[i] = (v[i] - med) / mad
    return out


def find_peaks(db, chat_counts, cfg):
    """Retorna [(segundo, score)] dos melhores momentos."""
    n = len(db)
    score = robust_z(smooth(db, 3))
    if chat_counts is not None and chat_counts.sum() > 20:
        d = int(cfg.get("chat_delay_seconds", 8))
        shifted = np.zeros(n)
        shifted[: max(0, n - d)] = chat_counts[d:n]
        score = score + cfg.get("chat_weight", 1.0) * robust_z(smooth(shifted, 5))
    pre, dur = cfg["clip_pre_seconds"], cfg["clip_seconds"]
    picks = []
    for i in np.argsort(-score):
        if score[i] < cfg["min_score"] or len(picks) >= cfg["clips_per_run"]:
            break
        if i - pre < 0 or i - pre + dur > n:
            continue
        if all(abs(i - j) >= cfg["min_gap_seconds"] for j, _ in picks):
            picks.append((int(i), float(score[i])))
    return sorted(picks)
