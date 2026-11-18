import os, shutil, sys, time, traceback
from pathlib import Path
import yaml

from . import state, record, detect, render, captions, meta, publish
from .chat import TwitchChat


def log(*a):
    print(*a, flush=True)


def normalize(ch):
    """Aceita so o link (string) ou dict antigo {name, platform}."""
    from urllib.parse import urlparse
    if isinstance(ch, dict):
        return ch
    u = ch.strip()
    if not u.startswith("http"):
        u = "https://" + u
    pr = urlparse(u)
    host, parts = pr.netloc.lower().replace("www.", ""), [x for x in pr.path.split("/") if x]
    if "twitch.tv" in host and parts:
        return {"name": parts[0], "platform": "twitch", "url": f"https://twitch.tv/{parts[0]}"}
    if "kick.com" in host and parts:
        return {"name": parts[0], "platform": "kick", "url": f"https://kick.com/{parts[0]}"}
    if "youtube.com" in host or "youtu.be" in host:
        if parts and parts[-1] not in ("live",) and "watch" not in parts and "youtu.be" not in host:
            u = u.rstrip("/") + "/live"
        name = next((p for p in parts if p.startswith("@")), "youtube" if (not parts or parts[0] == "watch") else parts[0])
        return {"name": name, "platform": "youtube", "url": u}
    raise ValueError(f"link nao reconhecido: {ch}")


def channel_url(ch):
    if ch.get("url"):
        return ch["url"]
    n, p = ch["name"], ch["platform"]
    if p == "twitch":
        return f"https://twitch.tv/{n}"
    if p == "kick":
        return f"https://kick.com/{n}"
    return f"https://www.youtube.com/{n if n.startswith('@') else '@' + n}/live"


def process_channel(ch, cfg, st, pub):
    url, name = channel_url(ch), ch["name"]
    work, out = Path("work"), Path("out")
    work.mkdir(exist_ok=True)
    out.mkdir(exist_ok=True)
    rec = str(work / "rec.ts")

    chat = None
    if ch["platform"] == "twitch" and cfg.get("chat_weight", 0) > 0:
        chat = TwitchChat(name)
        chat.start()
    log(f"[{name}] gravando {cfg['record_minutes']} min...")
    f = record.record(url, rec, cfg["record_minutes"], cfg["quality"])
    if chat:
        chat.stop_flag = True
    if not f:
        log(f"[{name}] gravacao vazia, pulando")
        return

    db = detect.audio_db(f)
    if len(db) == 0:
        log(f"[{name}] gravacao curta demais")
        return
    peaks = detect.find_peaks(db, chat.per_second(len(db)) if chat else None, cfg)
    log(f"[{name}] {len(peaks)} momento(s) encontrado(s): {[(t, round(s, 1)) for t, s in peaks]}")

    for t, score in peaks:
        start = t - cfg["clip_pre_seconds"]
        cid = f"{name.lstrip('@')}-{int(time.time())}-{t}"
        clip = out / f"{cid}.mp4"
        try:
            wav = str(work / "seg.wav")
            render.extract_wav(f, start, cfg["clip_seconds"], wav)
            ass, text = None, ""
            try:
                ass_path, text = captions.transcribe_to_ass(wav, str(work / "cap.ass"), cfg["whisper_model"])
                ass = "cap.ass" if ass_path else None
            except Exception:
                log("legenda falhou, seguindo sem:", traceback.format_exc(limit=2))
            render.render(f, start, cfg["clip_seconds"], str(clip), ass, workdir=str(work))
            m = meta.build(name, url, text, cfg)
            log(f"[{name}] clipe pronto: {clip.name} | {m['title']}")
        except Exception:
            log("falha ao renderizar:", traceback.format_exc(limit=3))
            continue

        posted = {}
        can_post = state.count_today(st) < cfg["max_posts_per_day"]
        for plat, fn in (("youtube", publish.youtube), ("tiktok", publish.tiktok), ("instagram", publish.instagram)):
            if pub[plat] and can_post:
                try:
                    posted[plat] = fn(str(clip), m)
                    log(f"[{name}] publicado em {plat}: {posted[plat]}")
                except Exception as e:
                    log(f"[{name}] erro em {plat}: {e}")
        if pub["telegram"]:
            try:
                publish.telegram(str(clip), m)
            except Exception as e:
                log(f"erro telegram: {e}")
        if posted:
            state.add(st, {"id": cid, "channel": name, **posted})
        state.save(st)
    os.remove(f)


def main():
    cfg = yaml.safe_load(open("config.yml", encoding="utf-8"))
    cfg["channels"] = [normalize(c) for c in cfg["channels"] if c]
    test = os.environ.get("TEST_MODE") == "1"
    if test:  # teste ponta a ponta: grava pouco, sempre gera 1 clipe, manda so pro Telegram
        cfg.update(record_minutes=4, min_score=-99, clips_per_run=1, max_posts_per_day=0)
        log("MODO TESTE: 4 min, 1 clipe, so Telegram")
    st = state.load()
    pub = publish.enabled(cfg)
    log("publicadores ativos:", pub)
    chs = cfg["channels"]
    off = st["runs"] % len(chs)
    live = []
    for ch in chs[off:] + chs[:off]:
        if len(live) >= cfg.get("max_channels_per_run", 1):
            break
        if record.is_live(channel_url(ch)):
            live.append(ch)
    st["runs"] += 1
    state.save(st)
    if not live:
        log("nenhum canal ao vivo agora")
        return
    for ch in live:
        process_channel(ch, cfg, st, pub)
    shutil.rmtree("work", ignore_errors=True)


if __name__ == "__main__":
    main()
