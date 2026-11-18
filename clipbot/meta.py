import re


def build(channel, url, transcript, cfg):
    words = re.sub(r"\s+", " ", transcript).strip().split()
    hook = " ".join(words[:7]).strip(" ,.-!?") if len(words) >= 3 else ""
    hook = hook[:1].upper() + hook[1:] if hook else cfg["fallback_title"]
    tag_ch = "#" + re.sub(r"[^A-Za-z0-9]", "", channel)
    tags = list(dict.fromkeys(cfg["hashtags"] + ([tag_ch] if len(tag_ch) > 2 else [])))
    title = f"{hook} {' '.join(tags[:3])}"[:100]
    caption = f"{hook}\n\nClip: {channel}\n{' '.join(tags)}"
    desc = f"{hook}\n\nClip da live de {channel} ({url})\n\n{' '.join(tags)} #Shorts"
    return {"title": title, "caption": caption, "description": desc,
            "yt_tags": [t.lstrip('#') for t in tags]}
