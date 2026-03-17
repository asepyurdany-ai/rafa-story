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


def get_background_video(content_type: str) -> str:
    """Pick appropriate background video based on content type.
    Prefers real Pixabay downloads; falls back to gradient placeholders.
    """
    # Real videos (from Pixabay) preferred
    real_mapping = {
        "quotes": ["mosque.mp4", "stars_night.mp4"],
        "hadist": ["mosque.mp4", "desert_sunset.mp4"],
        "kisah": ["desert_sunset.mp4", "stars_night.mp4", "mosque.mp4"],
    }
    # Gradient fallbacks
    fallback_mapping = {
        "quotes": ["mosque_gradient.mp4", "stars_gradient.mp4"],
        "hadist": ["mosque_gradient.mp4", "desert_gradient.mp4"],
        "kisah": ["desert_gradient.mp4", "stars_gradient.mp4", "mosque_gradient.mp4"],
    }

    for name in real_mapping.get(content_type, ["mosque.mp4"]):
        path = os.path.join(BACKGROUNDS_DIR, name)
        if os.path.exists(path):
            print(f"[VideoMaker] Using real background: {name}")
            return path

    for name in fallback_mapping.get(content_type, ["mosque_gradient.mp4"]):
        path = os.path.join(BACKGROUNDS_DIR, name)
        if os.path.exists(path):
            print(f"[VideoMaker] Using gradient fallback: {name}")
            return path

    # Last resort: any mp4
    backgrounds = list(Path(BACKGROUNDS_DIR).glob("*.mp4"))
    if backgrounds:
        chosen = str(random.choice(backgrounds))
        print(f"[VideoMaker] Using random background: {os.path.basename(chosen)}")
        return chosen

    raise FileNotFoundError("No background videos found in assets/backgrounds/")


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


def render_text_card(content: dict, tmp_dir: str) -> str:
    """
    Render a text card using Pillow.
    Returns path to the PNG image.
    """
    print("[VideoMaker] Rendering text card...")

    # Card dimensions
    card_width = 960
    card_padding = 48
    text_area_width = card_width - (card_padding * 2)

    # Determine font sizes
    text = content.get("text", "")
    text_len = len(text)

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

    # Wrap text
    wrapped_lines = wrap_text(text, font_text, text_area_width)

    # Calculate card height
    line_height_text = font_size_text + 12
    line_height_label = font_size_label + 16

    card_height = card_padding  # top
    card_height += line_height_label  # label
    card_height += 20  # separator space
    if title:
        card_height += line_height_label  # title
        card_height += 12
    card_height += len(wrapped_lines) * line_height_text  # text lines
    if source:
        card_height += 24  # gap
        card_height += font_size_source + 8  # source
    card_height += card_padding  # bottom

    # Create full image
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw card background (semi-transparent dark)
    card_x = (WIDTH - card_width) // 2
    card_y = (HEIGHT - card_height) // 2

    # Rounded rectangle card background
    card_bg = Image.new("RGBA", (card_width, card_height), (0, 0, 0, 0))
    card_draw = ImageDraw.Draw(card_bg)

    # Draw rounded rect with gradient
    radius = 32
    card_draw.rounded_rectangle(
        [0, 0, card_width - 1, card_height - 1],
        radius=radius,
        fill=(10, 10, 40, 200)
    )

    # Gold border
    card_draw.rounded_rectangle(
        [2, 2, card_width - 3, card_height - 3],
        radius=radius - 2,
        outline=(212, 175, 55, 180),
        width=3
    )

    img.paste(card_bg, (card_x, card_y), card_bg)
    draw = ImageDraw.Draw(img)

    # --- Draw label ---
    y_cursor = card_y + card_padding

    def draw_text_with_shadow(draw, x, y, text, font, fill=(255, 255, 255), shadow_offset=3, anchor="mm"):
        # Shadow
        draw.text((x + shadow_offset, y + shadow_offset), text, font=font,
                  fill=(0, 0, 0, 160), anchor=anchor)
        # Main text
        draw.text((x, y), text, font=font, fill=fill, anchor=anchor)

    # Label centered
    label_x = WIDTH // 2
    label_y = y_cursor + font_size_label // 2
    draw_text_with_shadow(draw, label_x, label_y, label, font_label,
                          fill=(212, 175, 55), anchor="mm")  # Gold label
    y_cursor += line_height_label + 8

    # Separator line
    sep_x1 = card_x + card_padding
    sep_x2 = card_x + card_width - card_padding
    draw.line([(sep_x1, y_cursor), (sep_x2, y_cursor)], fill=(212, 175, 55, 120), width=1)
    y_cursor += 16

    # Title if exists
    if title:
        title_x = WIDTH // 2
        title_y = y_cursor + font_size_label // 2
        draw_text_with_shadow(draw, title_x, title_y, title, font_label,
                              fill=(255, 220, 100), anchor="mm")
        y_cursor += line_height_label + 8

    # Text lines
    for line in wrapped_lines:
        line_x = WIDTH // 2
        line_y = y_cursor + font_size_text // 2
        draw_text_with_shadow(draw, line_x, line_y, line, font_text,
                              fill=(255, 255, 255), anchor="mm")
        y_cursor += line_height_text

    # Source
    if source:
        y_cursor += 16
        source_x = WIDTH // 2
        source_y = y_cursor + font_size_source // 2
        draw_text_with_shadow(draw, source_x, source_y, source, font_source,
                              fill=(180, 200, 255), anchor="mm")

    # --- Watermark bottom right ---
    wm_x = WIDTH - 40
    wm_y = HEIGHT - 60
    draw_text_with_shadow(draw, wm_x, wm_y, WATERMARK, font_watermark,
                          fill=(255, 255, 255, 200), anchor="rm")

    # Save card as PNG
    card_path = os.path.join(tmp_dir, "text_card.png")
    img.save(card_path, "PNG")
    print(f"[VideoMaker] Text card saved: {card_path} ({img.size})")
    return card_path


def make_video(content: dict, output_path: str) -> str:
    """
    Generate full video with background, text overlay, and optional music.
    """
    print(f"[VideoMaker] Generating video for type: {content.get('type', 'unknown')}")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    bg_video = get_background_video(content.get("type", "quotes"))
    music_file = get_music_file()

    print(f"[VideoMaker] Background: {bg_video}")
    print(f"[VideoMaker] Music: {music_file or 'None (silent)'}")

    with tempfile.TemporaryDirectory() as tmp_dir:
        # Step 1: Render text card
        card_path = render_text_card(content, tmp_dir)

        # Step 2: Build ffmpeg command
        # Background: loop + scale to 1080x1920
        # Overlay text card centered
        # Add dark gradient overlay for readability
        # Watermark already in card

        filter_complex = (
            # Scale background to cover 1080x1920
            "[0:v]loop=loop=-1:size=1500:start=0,"
            "scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,"
            "setsar=1,"
            # Darken bg for readability
            "eq=brightness=-0.15:saturation=0.7"
            "[bg];"
            # Text card overlay - centered
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
            filter_complex += ";[2:a]volume=0.2[aout]"
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
            # Silent audio — anullsrc must be declared as input BEFORE output options
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
    # Quick test
    from content_generator import get_random_content

    content = get_random_content("quotes")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = os.path.join(OUTPUT_DIR, f"test_{ts}.mp4")
    make_video(content, out)
    print(f"Output: {out}")
