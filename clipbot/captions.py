_model = None

HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Liberation Sans,88,&H0000F0FF,&H000000FF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,7,2,2,60,60,420,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _t(t):
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def transcribe_to_ass(wav, ass_path, model_name="base"):
    """Gera legenda estilo TikTok (3 palavras por vez). Retorna o texto transcrito."""
    global _model
    from faster_whisper import WhisperModel
    if _model is None:
        _model = WhisperModel(model_name, device="cpu", compute_type="int8")
    segs, _ = _model.transcribe(wav, word_timestamps=True, vad_filter=True, beam_size=1)
    words = [(w.start, w.end, w.word.strip()) for s in segs for w in (s.words or []) if w.word.strip()]
    if not words:
        return None, ""
    lines = []
    for i in range(0, len(words), 3):
        grp = words[i:i + 3]
        start = grp[0][0]
        end = words[i + 3][0] if i + 3 < len(words) else grp[-1][1] + 0.3
        text = " ".join(w[2] for w in grp).upper().replace("{", "").replace("}", "")
        lines.append(f"Dialogue: 0,{_t(start)},{_t(end)},Default,,0,0,0,,{text}")
    open(ass_path, "w", encoding="utf-8").write(HEADER + "\n".join(lines) + "\n")
    return ass_path, " ".join(w[2] for w in words)
