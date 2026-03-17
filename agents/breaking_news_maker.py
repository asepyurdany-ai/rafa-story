"""
breaking_news_maker.py - Generate breaking news style geopolitik videos
Format: cinematic military footage + dramatic text overlay
"""
import os
import sys
import json
import random
import subprocess
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
BACKGROUNDS_DIR = os.path.join(ASSETS_DIR, "backgrounds")
FONT_PATH = os.path.join(ASSETS_DIR, "fonts", "DejaVuSans-Bold.ttf")
CONTENT_PATH = os.path.join(BASE_DIR, "content", "geopolitik.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

FFMPEG = os.environ.get("FFMPEG", "/home/asepyudi/bin/ffmpeg")
WIDTH, HEIGHT = 1080, 1920
DURATION = 45
FPS = 30
WATERMARK = "@fakhry831"

MILITARY_BACKGROUNDS = [
    "bg_jet.mp4", "bg_warship.mp4", "bg_missile.mp4",
    "bg_helicopter.mp4", "bg_explosion.mp4"
]

_last_bg = None

def get_military_background():
    global _last_bg
    candidates = []
    for name in MILITARY_BACKGROUNDS:
        path = os.path.join(BACKGROUNDS_DIR, name)
        if os.path.exists(path):
            candidates.append(path)
    if not candidates:
        # Fallback to any bg
        candidates = [str(p) for p in Path(BACKGROUNDS_DIR).glob("bg_*.mp4")]
    if _last_bg and len(candidates) > 1:
        candidates = [c for c in candidates if c != _last_bg]
    chosen = random.choice(candidates)
    _last_bg = chosen
    print(f"[BreakingNews] Background: {os.path.basename(chosen)}")
    return chosen


def load_geopolitik():
    with open(CONTENT_PATH, encoding="utf-8") as f:
        return json.load(f)


def get_random_geopolitik():
    items = load_geopolitik()
    item = random.choice(items)
    item["type"] = "geopolitik"
    return item


def _wrap_text(text, font, max_width, draw):
    lines = []
    for paragraph in text.split('\n'):
        if not paragraph.strip():
            lines.append('')
            continue
        words = paragraph.split()
        current = ''
        for word in words:
            test = f"{current} {word}".strip()
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
    return lines


def render_breaking_news_frame(content: dict, text_override: str = None, progress: float = 1.0) -> Image.Image:
    """Render a breaking news style card."""
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    label = content.get("label", "⚡ BREAKING")
    title = content.get("title", "")
    teks = text_override if text_override is not None else content.get("teks", "")
    pertanyaan = content.get("pertanyaan", "")

    try:
        font_label = ImageFont.truetype(FONT_PATH, 42)
        font_title = ImageFont.truetype(FONT_PATH, 52)
        font_body = ImageFont.truetype(FONT_PATH, 36)
        font_question = ImageFont.truetype(FONT_PATH, 44)
        font_wm = ImageFont.truetype(FONT_PATH, 34)
    except:
        font_label = font_title = font_body = font_question = font_wm = ImageFont.load_default()

    card_w = 1000
    card_x = (WIDTH - card_w) // 2
    pad = 40

    # Estimate card height
    body_lines = _wrap_text(teks, font_body, card_w - pad * 2, draw)
    q_lines = _wrap_text(pertanyaan, font_question, card_w - pad * 2, draw)
    line_h_body = 48
    line_h_q = 56
    card_h = pad + 56 + 16 + 60 + 16 + 2 + 16 + (len(body_lines) * line_h_body) + 24 + (len(q_lines) * line_h_q) + pad
    card_y = (HEIGHT - card_h) // 2

    # Dark semi-transparent card background
    card_bg = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    card_draw = ImageDraw.Draw(card_bg)
    card_draw.rounded_rectangle([0, 0, card_w - 1, card_h - 1], radius=16, fill=(5, 5, 20, 210))
    # Red accent line on left
    card_draw.rectangle([0, 0, 6, card_h - 1], fill=(220, 30, 30, 255))
    # Gold border
    card_draw.rounded_rectangle([8, 2, card_w - 3, card_h - 3], radius=14, outline=(220, 30, 30, 160), width=2)
    img.paste(card_bg, (card_x, card_y), card_bg)

    draw = ImageDraw.Draw(img)
    y = card_y + pad

    def shadow_text(x, y, text, font, fill, anchor="lm", shadow=(0,0,0,180)):
        draw.text((x+2, y+2), text, font=font, fill=shadow, anchor=anchor)
        draw.text((x, y), text, font=font, fill=fill, anchor=anchor)

    # BREAKING label (red)
    shadow_text(card_x + pad + 10, y + 28, label, font_label, fill=(255, 60, 60, 255), anchor="lm")
    y += 56 + 16

    # Title (white/gold)
    title_lines = _wrap_text(title, font_title, card_w - pad * 2 - 10, draw)
    for tl in title_lines:
        shadow_text(WIDTH // 2, y + 30, tl, font_title, fill=(255, 220, 80, 255), anchor="mm")
        y += 60
    y += 16

    # Separator line
    draw.line([(card_x + pad, y), (card_x + card_w - pad, y)], fill=(220, 30, 30, 180), width=2)
    y += 16

    # Body text (typewriter style based on progress)
    full_teks = content.get("teks", "")
    show_len = int(len(full_teks) * min(progress, 0.9)) if progress < 1.0 else len(full_teks)
    display_teks = full_teks[:show_len] + ("|" if progress < 1.0 else "")
    body_lines_display = _wrap_text(display_teks, font_body, card_w - pad * 2 - 10, draw)

    for bl in body_lines_display:
        if not bl:
            y += line_h_body // 2
            continue
        shadow_text(card_x + pad + 10, y + line_h_body // 2, bl, font_body, fill=(230, 230, 230, 255), anchor="lm")
        y += line_h_body
    y += 24

    # Question (show only after typing done)
    if progress >= 0.9:
        q_alpha = int(255 * min(1.0, (progress - 0.9) / 0.1))
        for ql in q_lines:
            shadow_text(WIDTH // 2, y + line_h_q // 2, ql, font_question,
                       fill=(255, 200, 50, q_alpha), anchor="mm")
            y += line_h_q

    # Watermark
    shadow_text(WIDTH - 40, HEIGHT - 55, WATERMARK, font_wm, fill=(255, 255, 255, 200), anchor="rm")

    return img


def make_breaking_news_video(content: dict, output_path: str) -> str:
    """Generate breaking news video with typewriter effect."""
    bg_video = get_military_background()

    with tempfile.TemporaryDirectory() as tmp_dir:
        frames_dir = os.path.join(tmp_dir, "frames")
        os.makedirs(frames_dir)

        # Generate frames: typewriter effect for body text
        n_frames = DURATION * FPS
        typing_frames = int(n_frames * 0.55)  # typing at 55% of duration
        hold_frames = n_frames - typing_frames

        print(f"[BreakingNews] Rendering {typing_frames} typing frames + {hold_frames} hold frames...")

        # Render unique stages (not every frame — step for perf)
        full_text = content.get("teks", "")
        text_len = len(full_text)
        step = max(1, text_len // 60)  # ~60 unique stages
        stages = list(range(step, text_len + 1, step))
        if not stages or stages[-1] < text_len:
            stages.append(text_len)

        stage_imgs = {}
        for i, chars in enumerate(stages):
            progress = chars / text_len * 0.9  # 0 to 0.9
            img = render_breaking_news_frame(content, progress=progress)
            path = os.path.join(frames_dir, f"stage_{i:04d}.png")
            img.save(path, "PNG")
            stage_imgs[chars] = path

        # Hold frame (full text + question)
        hold_img = render_breaking_news_frame(content, progress=1.0)
        hold_path = os.path.join(frames_dir, "hold.png")
        hold_img.save(hold_path, "PNG")

        # Write concat list
        concat_path = os.path.join(tmp_dir, "concat.txt")
        stage_duration = (DURATION * 0.55) / len(stages)
        hold_duration = DURATION * 0.45

        with open(concat_path, "w") as f:
            for path in stage_imgs.values():
                f.write(f"file '{path}'\n")
                f.write(f"duration {stage_duration:.4f}\n")
            f.write(f"file '{hold_path}'\n")
            f.write(f"duration {hold_duration:.4f}\n")
            f.write(f"file '{hold_path}'\n")  # ffmpeg requires last entry without duration

        print(f"[BreakingNews] Building video (single-pass)...")

        filter_complex = (
            "[0:v]loop=loop=-1:size=1500:start=0,"
            "scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,setsar=1,"
            "eq=brightness=-0.05:saturation=1.2,hue=s=1.1"  # slightly more vivid
            "[bg];"
            "[1:v]scale=1080:1920:force_original_aspect_ratio=decrease,"
            "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black@0,setsar=1[overlay];"
            "[bg][overlay]overlay=0:0:format=auto[out]"
        )

        cmd = [
            FFMPEG, "-y",
            "-stream_loop", "-1", "-i", bg_video,
            "-f", "concat", "-safe", "0", "-i", concat_path,
            "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
            "-filter_complex", filter_complex,
            "-map", "[out]", "-map", "2:a",
            "-t", str(DURATION),
            "-r", str(FPS),
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "64k",
            "-movflags", "+faststart",
            output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[BreakingNews] ffmpeg error:\n{result.stderr[-2000:]}")
            raise RuntimeError("ffmpeg failed")

        size_mb = os.path.getsize(output_path) / 1024 / 1024
        print(f"[BreakingNews] ✅ Done! {size_mb:.1f} MB → {output_path}")
        return output_path


def generate_caption(content: dict) -> str:
    title = content.get("title", "")
    pertanyaan = content.get("pertanyaan", "")
    return (
        f"⚡ {title}\n\n"
        f"{pertanyaan}\n\n"
        f"Tulis pendapat kamu di kolom komentar! 👇\n\n"
        f"#perangdunia3 #iranisrael #geopolitik #breakingnews #fyp #fypシ #viral #berita #timurtengah #politik"
    )


if __name__ == "__main__":
    import sys
    from datetime import datetime
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    content = get_random_geopolitik()
    print(f"Content: {content['title']}")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = os.path.join(OUTPUT_DIR, f"geopolitik_{ts}.mp4")
    make_breaking_news_video(content, out)
    caption = generate_caption(content)
    print(f"\n📝 Caption:\n{caption}")
