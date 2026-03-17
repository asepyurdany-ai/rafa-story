"""
video_maker.py - Generate Islamic storytelling videos for TikTok @fakhry831
"""
import os
import sys
import math
import random
import subprocess
import textwrap
import tempfile
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
FFMPEG = "/home/asepyudi/bin/ffmpeg"

FONT_PATH = os.path.join(ASSETS_DIR, "fonts", "DejaVuSans-Bold.ttf")
BACKGROUNDS_DIR = os.path.join(ASSETS_DIR, "backgrounds")
MUSIC_DIR = os.path.join(ASSETS_DIR, "music")

# Video specs
WIDTH = 1080
HEIGHT = 1920
DURATION = 45
FPS = 25

# Watermark
WATERMARK = "@fakhry831"

# Typewriter settings
TYPEWRITER_FPS = 15           # fps for typewriter frame sequence
TYPEWRITER_TYPING_RATIO = 0.25  # typing completes at this fraction of video (faster!)


_last_background = None  # Track last used to avoid repeats

def get_background_video(content_type: str) -> str:
    """Pick background video — avoids repeating the same one consecutively."""
    global _last_background

    all_backgrounds = sorted(Path(BACKGROUNDS_DIR).glob("bg_*.mp4"))
    if not all_backgrounds:
        raise FileNotFoundError("No background videos found in assets/backgrounds/")

    # Convert to strings
    candidates = [str(p) for p in all_backgrounds]

    # Exclude last used if we have enough options
    if _last_background and len(candidates) > 1:
        candidates = [c for c in candidates if c != _last_background]

    chosen = random.choice(candidates)
    _last_background = chosen
    print(f"[VideoMaker] Background: {os.path.basename(chosen)}")
    return chosen


def get_music_file() -> str | None:
    """Find music file if available."""
    if not os.path.exists(MUSIC_DIR):
        return None
    music_files = list(Path(MUSIC_DIR).glob("*.mp3")) + list(Path(MUSIC_DIR).glob("*.m4a"))
    if music_files:
        return str(music_files[0])
    return None


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """Wrap text to fit within max_width pixels."""
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = f"{current_line} {word}".strip()
        bbox = font.getbbox(test_line)
        line_width = bbox[2] - bbox[0]
        if line_width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines


def _render_card_image(content: dict, text_override: str | None = None, show_cursor: bool = False) -> Image.Image:
    """
    Core card rendering. Returns a PIL RGBA Image.
    text_override: if set, use this text instead of content['text']
    show_cursor: if True, append a blinking cursor '|' to the text
    """
    card_width = 960
    card_padding = 48
    text_area_width = card_width - (card_padding * 2)

    text = text_override if text_override is not None else content.get("text", "")
    display_text = text + "|" if show_cursor else text
    text_len = len(content.get("text", ""))  # use full text length for font sizing

    if text_len <= 80:
        font_size_text = 48
    elif text_len <= 150:
        font_size_text = 40
    else:
        font_size_text = 34

    font_size_label = 36
    font_size_source = 30
    font_size_watermark = 38

    try:
        font_label = ImageFont.truetype(FONT_PATH, font_size_label)
        font_text = ImageFont.truetype(FONT_PATH, font_size_text)
        font_source = ImageFont.truetype(FONT_PATH, font_size_source)
        font_watermark = ImageFont.truetype(FONT_PATH, font_size_watermark)
    except Exception as e:
        print(f"[VideoMaker] Font load error: {e}, using default")
        font_label = ImageFont.load_default()
        font_text = ImageFont.load_default()
        font_source = ImageFont.load_default()
        font_watermark = ImageFont.load_default()

    label = content.get("label", "📖 Konten Islam")
    source = content.get("source", "")
    title = content.get("title", "")

    wrapped_lines = wrap_text(display_text, font_text, text_area_width)

    line_height_text = font_size_text + 12
    line_height_label = font_size_label + 16

    card_height = card_padding
    card_height += line_height_label
    card_height += 20
    if title:
        card_height += line_height_label + 12
    card_height += len(wrapped_lines) * line_height_text
    if source:
        card_height += 24 + font_size_source + 8
    card_height += card_padding

    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    card_x = (WIDTH - card_width) // 2
    card_y = (HEIGHT - card_height) // 2

    card_bg = Image.new("RGBA", (card_width, card_height), (0, 0, 0, 0))
    card_draw = ImageDraw.Draw(card_bg)

    radius = 32
    card_draw.rounded_rectangle(
        [0, 0, card_width - 1, card_height - 1],
        radius=radius,
        fill=(10, 10, 40, 200)
    )
    card_draw.rounded_rectangle(
        [2, 2, card_width - 3, card_height - 3],
        radius=radius - 2,
        outline=(212, 175, 55, 180),
        width=3
    )

    img.paste(card_bg, (card_x, card_y), card_bg)
    draw = ImageDraw.Draw(img)

    y_cursor = card_y + card_padding

    def draw_text_with_shadow(draw, x, y, text, font, fill=(255, 255, 255), shadow_offset=3, anchor="mm"):
        draw.text((x + shadow_offset, y + shadow_offset), text, font=font,
                  fill=(0, 0, 0, 160), anchor=anchor)
        draw.text((x, y), text, font=font, fill=fill, anchor=anchor)

    label_x = WIDTH // 2
    label_y = y_cursor + font_size_label // 2
    draw_text_with_shadow(draw, label_x, label_y, label, font_label,
                          fill=(212, 175, 55), anchor="mm")
    y_cursor += line_height_label + 8

    sep_x1 = card_x + card_padding
    sep_x2 = card_x + card_width - card_padding
    draw.line([(sep_x1, y_cursor), (sep_x2, y_cursor)], fill=(212, 175, 55, 120), width=1)
    y_cursor += 16

    if title:
        title_x = WIDTH // 2
        title_y = y_cursor + font_size_label // 2
        draw_text_with_shadow(draw, title_x, title_y, title, font_label,
                              fill=(255, 220, 100), anchor="mm")
        y_cursor += line_height_label + 8

    for line in wrapped_lines:
        line_x = WIDTH // 2
        line_y = y_cursor + font_size_text // 2
        draw_text_with_shadow(draw, line_x, line_y, line, font_text,
                              fill=(255, 255, 255), anchor="mm")
        y_cursor += line_height_text

    if source:
        y_cursor += 16
        source_x = WIDTH // 2
        source_y = y_cursor + font_size_source // 2
        draw_text_with_shadow(draw, source_x, source_y, source, font_source,
                              fill=(180, 200, 255), anchor="mm")

    wm_x = WIDTH - 40
    wm_y = HEIGHT - 60
    draw_text_with_shadow(draw, wm_x, wm_y, WATERMARK, font_watermark,
                          fill=(255, 255, 255, 200), anchor="rm")

    return img


def render_text_card(content: dict, tmp_dir: str) -> str:
    """
    Render a text card using Pillow (full text, no typewriter).
    Returns path to the PNG image.
    """
    print("[VideoMaker] Rendering text card...")
    img = _render_card_image(content)
    card_path = os.path.join(tmp_dir, "text_card.png")
    img.save(card_path, "PNG")
    print(f"[VideoMaker] Text card saved: {card_path} ({img.size})")
    return card_path


def generate_typewriter_frames(content: dict, frames_dir: str, duration: int = DURATION) -> str:
    """
    Generate PNG frames for typewriter effect.
    Returns path to ffmpeg concat list file.
    """
    text = content.get("text", "")
    text_len = len(text)

    # Total frames at TYPEWRITER_FPS
    total_frames = duration * TYPEWRITER_FPS
    typing_frames = int(total_frames * TYPEWRITER_TYPING_RATIO)
    hold_frames = total_frames - typing_frames

    # Unique text stages: add every N chars to keep frame count reasonable
    # Aim for at most ~100 unique rendered stages
    max_stages = min(100, text_len)
    step = max(1, text_len // max_stages)

    # Build list of char counts for each stage
    stages = list(range(step, text_len + 1, step))
    if not stages or stages[-1] < text_len:
        stages.append(text_len)

    n_stages = len(stages)
    print(f"[VideoMaker] Typewriter: {text_len} chars, {n_stages} unique stages, step={step}")
    print(f"[VideoMaker] Rendering {n_stages} frame PNGs into {frames_dir}...")

    os.makedirs(frames_dir, exist_ok=True)

    # Render each unique stage
    stage_paths = []
    for i, char_count in enumerate(stages):
        partial = text[:char_count]
        is_last = (char_count == text_len)
        show_cursor = not is_last  # show cursor while typing, hide when complete
        img = _render_card_image(content, text_override=partial, show_cursor=show_cursor)
        frame_path = os.path.join(frames_dir, f"stage_{i:04d}.png")
        img.save(frame_path, "PNG")
        stage_paths.append(frame_path)

    # Also render final "hold" frame (full text, no cursor)
    final_img = _render_card_image(content, text_override=text, show_cursor=False)
    final_path = os.path.join(frames_dir, "stage_final.png")
    final_img.save(final_path, "PNG")

    print(f"[VideoMaker] Rendered {n_stages + 1} frames")

    # Calculate per-stage duration for typing phase
    # Each stage gets equal time during the typing period
    stage_duration = (duration * TYPEWRITER_TYPING_RATIO) / n_stages
    hold_duration = duration * (1.0 - TYPEWRITER_TYPING_RATIO)

    # Build ffmpeg concat list
    concat_path = os.path.join(frames_dir, "concat.txt")
    with open(concat_path, "w") as f:
        for path in stage_paths:
            f.write(f"file '{path}'\n")
            f.write(f"duration {stage_duration:.4f}\n")
        # Hold frame
        f.write(f"file '{final_path}'\n")
        f.write(f"duration {hold_duration:.4f}\n")
        # ffmpeg concat requires last file repeated without duration
        f.write(f"file '{final_path}'\n")

    print(f"[VideoMaker] Concat list written: {concat_path}")
    return concat_path


def make_video_typewriter(content: dict, bg_video: str, music_file: str | None, output_path: str) -> str:
    """
    Build a typewriter-effect video for quotes/hadist types.
    """
    import tempfile as tf

    with tf.TemporaryDirectory() as tmp_dir:
        frames_dir = os.path.join(tmp_dir, "frames")
        concat_path = generate_typewriter_frames(content, frames_dir, DURATION)

        # Single-pass: bg video + RGBA image sequence overlay + music
        # Avoid 2-pass alpha encoding issue (h264 drops alpha → black bg)
        print("[VideoMaker] Building typewriter video (single-pass)...")

        filter_complex = (
            "[0:v]loop=loop=-1:size=1500:start=0,"
            "scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,setsar=1,"
            "eq=brightness=-0.1:saturation=0.8[bg];"
            "[1:v]scale=1080:1920:force_original_aspect_ratio=decrease,"
            "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black@0,setsar=1[overlay];"
            "[bg][overlay]overlay=0:0:format=auto[out]"
        )

        cmd = [
            FFMPEG, "-y",
            "-stream_loop", "-1",
            "-i", bg_video,
            "-f", "concat", "-safe", "0", "-i", concat_path,
        ]

        if music_file:
            cmd += ["-i", music_file]
            filter_complex += ";[2:a]volume=0.6[aout]"
            cmd += [
                "-filter_complex", filter_complex,
                "-map", "[out]", "-map", "[aout]",
            ]
        else:
            cmd += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
            filter_complex += ";[2:a]anull[aout]"
            cmd += [
                "-filter_complex", filter_complex,
                "-map", "[out]", "-map", "[aout]",
            ]

        cmd += [
            "-t", str(DURATION),
            "-r", str(FPS),
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[VideoMaker] ffmpeg stderr:\n{result.stderr[-3000:]}")
            raise RuntimeError(f"ffmpeg typewriter failed: {result.returncode}")

        print(f"[VideoMaker] ✅ Typewriter video generated!")
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"[VideoMaker] File size: {size_mb:.1f} MB")
        return output_path


def make_video(content: dict, output_path: str) -> str:
    """
    Generate full video with background, text overlay, and optional music.
    Routes quotes/hadist to typewriter effect, kisah to standard rendering.
    """
    content_type = content.get("type", "quotes")
    print(f"[VideoMaker] Generating video for type: {content_type}")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    bg_video = get_background_video(content_type)
    music_file = None  # No music — Asep picks manually on TikTok

    print(f"[VideoMaker] Background: {bg_video}")
    print(f"[VideoMaker] Music: disabled (manual on TikTok)")

    # Route quotes and hadist to typewriter effect
    if content_type in ("quotes", "hadist"):
        print(f"[VideoMaker] Using typewriter effect for type: {content_type}")
        return make_video_typewriter(content, bg_video, music_file, output_path)

    # kisah and fallback: standard full-text card
    print(f"[VideoMaker] Using standard text card for type: {content_type}")
    with tempfile.TemporaryDirectory() as tmp_dir:
        card_path = render_text_card(content, tmp_dir)

        filter_complex = (
            "[0:v]loop=loop=-1:size=1500:start=0,"
            "scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,"
            "setsar=1,"
            "eq=brightness=-0.15:saturation=0.7"
            "[bg];"
            "[1:v]scale=1080:-1[card];"
            "[bg][card]overlay=(W-w)/2:(H-h)/2[out]"
        )

        cmd = [
            FFMPEG, "-y",
            "-stream_loop", "-1",
            "-i", bg_video,
            "-i", card_path,
        ]

        if music_file:
            cmd += ["-i", music_file]
            filter_complex += ";[2:a]volume=0.6[aout]"
            cmd += [
                "-filter_complex", filter_complex,
                "-map", "[out]",
                "-map", "[aout]",
                "-t", str(DURATION),
                "-r", str(FPS),
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-c:a", "aac",
                "-b:a", "128k",
                "-movflags", "+faststart",
                output_path
            ]
        else:
            cmd += [
                "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                "-filter_complex", filter_complex,
                "-map", "[out]",
                "-map", "2:a",
                "-t", str(DURATION),
                "-r", str(FPS),
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-c:a", "aac",
                "-b:a", "64k",
                "-movflags", "+faststart",
                output_path
            ]

        print(f"[VideoMaker] Running ffmpeg...")
        print(f"[VideoMaker] Output: {output_path}")

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"[VideoMaker] ffmpeg stderr:\n{result.stderr[-2000:]}")
            raise RuntimeError(f"ffmpeg failed with code {result.returncode}")

        print(f"[VideoMaker] ✅ Video generated successfully!")
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"[VideoMaker] File size: {size_mb:.1f} MB")
        return output_path


if __name__ == "__main__":
    from content_generator import get_random_content

    content = get_random_content("quotes")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = os.path.join(OUTPUT_DIR, f"test_{ts}.mp4")
    make_video(content, out)
    print(f"Output: {out}")
