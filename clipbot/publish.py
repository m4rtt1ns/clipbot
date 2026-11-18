import json, os, time
import requests


def _have(*names):
    return all(os.environ.get(n) for n in names)


def enabled(cfg):
    p = cfg.get("publish", {})
    return {
        "youtube": p.get("youtube") and _have("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN"),
        "tiktok": p.get("tiktok") and _have("TT_CLIENT_KEY", "TT_CLIENT_SECRET", "TT_REFRESH_TOKEN"),
        "instagram": p.get("instagram") and _have("IG_USER_ID", "IG_ACCESS_TOKEN"),
        "telegram": p.get("telegram") and _have("TG_BOT_TOKEN", "TG_CHAT_ID"),
    }


def youtube(path, meta):
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": os.environ["YT_CLIENT_ID"], "client_secret": os.environ["YT_CLIENT_SECRET"],
        "refresh_token": os.environ["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"}, timeout=30)
    r.raise_for_status()
    tok = r.json()["access_token"]
    body = {"snippet": {"title": meta["title"], "description": meta["description"],
                        "tags": meta["yt_tags"], "categoryId": "20"},
            "status": {"privacyStatus": os.environ.get("YT_PRIVACY", "public"),
                       "selfDeclaredMadeForKids": False}}
    size = os.path.getsize(path)
    init = requests.post(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8",
                 "X-Upload-Content-Length": str(size), "X-Upload-Content-Type": "video/mp4"},
        data=json.dumps(body), timeout=60)
    init.raise_for_status()
    with open(path, "rb") as f:
        up = requests.put(init.headers["Location"], data=f, timeout=900,
                          headers={"Content-Type": "video/mp4", "Content-Length": str(size)})
    up.raise_for_status()
    return up.json().get("id")


def tiktok(path, meta):
    r = requests.post("https://open.tiktokapis.com/v2/oauth/token/", data={
        "client_key": os.environ["TT_CLIENT_KEY"], "client_secret": os.environ["TT_CLIENT_SECRET"],
        "grant_type": "refresh_token", "refresh_token": os.environ["TT_REFRESH_TOKEN"]}, timeout=30)
    r.raise_for_status()
    tok = r.json()["access_token"]
    size = os.path.getsize(path)
    init = requests.post(
        "https://open.tiktokapis.com/v2/post/publish/video/init/",
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8"},
        data=json.dumps({
            "post_info": {"title": meta["caption"][:2000],
                          "privacy_level": os.environ.get("TT_PRIVACY", "SELF_ONLY")},
            "source_info": {"source": "FILE_UPLOAD", "video_size": size,
                            "chunk_size": size, "total_chunk_count": 1}}), timeout=60)
    init.raise_for_status()
    data = init.json()["data"]
    with open(path, "rb") as f:
        up = requests.put(data["upload_url"], data=f, timeout=900, headers={
            "Content-Type": "video/mp4", "Content-Length": str(size),
            "Content-Range": f"bytes 0-{size - 1}/{size}"})
    up.raise_for_status()
    return data.get("publish_id")


def telegram(path, meta):
    with open(path, "rb") as f:
        r = requests.post(f"https://api.telegram.org/bot{os.environ['TG_BOT_TOKEN']}/sendVideo",
                          data={"chat_id": os.environ["TG_CHAT_ID"], "caption": meta["caption"][:1000],
                                "supports_streaming": "true"},
                          files={"video": f}, timeout=300)
    r.raise_for_status()
    return True


def instagram(path, meta):
    """Reels via Graph API com upload resumavel (nao precisa de URL publica)."""
    v = os.environ.get("IG_GRAPH_VERSION", "v24.0")
    uid, tok = os.environ["IG_USER_ID"], os.environ["IG_ACCESS_TOKEN"]
    base = f"https://graph.facebook.com/{v}"
    r = requests.post(f"{base}/{uid}/media", timeout=60, data={
        "media_type": "REELS", "upload_type": "resumable", "share_to_feed": "true",
        "caption": meta["caption"][:2200], "access_token": tok})
    r.raise_for_status()
    cid = r.json()["id"]
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        up = requests.post(f"https://rupload.facebook.com/ig-api-upload/{v}/{cid}", data=f, timeout=900,
                           headers={"Authorization": f"OAuth {tok}", "offset": "0", "file_size": str(size)})
    up.raise_for_status()
    for _ in range(24):  # ate ~6 min
        time.sleep(15)
        s = requests.get(f"{base}/{cid}", params={"fields": "status_code", "access_token": tok}, timeout=30)
        s.raise_for_status()
        code = s.json().get("status_code")
        if code == "FINISHED":
            break
        if code in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"instagram container {code}: {s.text}")
    else:
        raise RuntimeError("instagram: processamento demorou demais")
    pub = requests.post(f"{base}/{uid}/media_publish", timeout=60,
                        data={"creation_id": cid, "access_token": tok})
    pub.raise_for_status()
    return pub.json().get("id")
