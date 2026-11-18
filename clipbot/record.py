import json, os, subprocess


def is_live(url):
    try:
        r = subprocess.run(["streamlink", "--json", url], capture_output=True, text=True, timeout=90)
        return bool(json.loads(r.stdout).get("streams"))
    except Exception:
        return False


def record(url, out, minutes, quality):
    h, m = divmod(int(minutes), 60)
    cmd = ["streamlink", url, quality, "-o", out, "-f", "--hls-duration", f"{h:02d}:{m:02d}:00",
           "--retry-streams", "5", "--retry-max", "3"]
    if "twitch.tv" in url:
        cmd.append("--twitch-disable-ads")
    try:
        subprocess.run(cmd, timeout=int(minutes) * 60 + 180)
    except subprocess.TimeoutExpired:
        pass
    return out if os.path.exists(out) and os.path.getsize(out) > 2_000_000 else None
