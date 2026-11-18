import json, time, pathlib

P = pathlib.Path("state.json")


def load():
    if P.exists():
        try:
            return json.loads(P.read_text())
        except Exception:
            pass
    return {"posted": [], "daily": {}, "runs": 0}


def save(s):
    P.write_text(json.dumps(s, indent=1, ensure_ascii=False))


def today():
    return time.strftime("%Y-%m-%d", time.gmtime())


def count_today(s):
    return s["daily"].get(today(), 0)


def add(s, record):
    s["posted"] = (s["posted"] + [record])[-200:]
    s["daily"][today()] = count_today(s) + 1
    s["daily"] = {k: v for k, v in sorted(s["daily"].items())[-7:]}
