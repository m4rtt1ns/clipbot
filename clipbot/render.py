import os, subprocess

LAYOUT = ("[0:v]split[a][b];"
          "[a]scale=108:192:force_original_aspect_ratio=increase,crop=108:192,boxblur=4:2,scale=1080:1920[bg];"
          "[b]scale=1080:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2")


def extract_wav(src, start, dur, wav):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(start), "-t", str(dur), "-i", src,
                    "-vn", "-ac", "1", "-ar", "16000", wav], check=True)


def render(src, start, dur, out, ass_name=None, workdir="."):
    """Corta e converte para 9:16 (fundo desfocado), queimando a legenda se houver."""
    vf = LAYOUT + (f",subtitles={ass_name}" if ass_name else "") + "[vo]"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(start), "-i", os.path.abspath(src), "-t", str(dur),
                    "-filter_complex", vf, "-map", "[vo]", "-map", "0:a?",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", os.path.abspath(out)],
                   check=True, cwd=workdir)
