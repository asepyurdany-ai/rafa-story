# rafa-story 🕌

**Islamic storytelling video pipeline for TikTok @fakhry831**

Generates short 30-60s vertical (9:16) videos with beautiful text overlays — quotes from the Sahabat Nabi, Hadist, and Kisah Nabi — ready to upload to TikTok.

---

## Features

- 🎬 **Auto video generation** — pick random content, render card, burn onto background
- 📖 **Rich content database** — 20+ quotes, 20+ hadist, 10+ kisah nabi (Indonesian)
- 🎨 **Beautiful text cards** — gold border, dark bg, white text with drop shadow
- 📱 **TikTok-ready** — 1080×1920 vertical, 45s, H.264/AAC
- 🌄 **Real backgrounds** — actual mosque, desert sunset, and stars footage from Pixabay

---

## Setup

```bash
cd /home/asepyudi/rafa-story

# Uses the klinik.financial venv (already has Pillow, anthropic, etc.)
/home/asepyudi/klinik.financial/.venv/bin/python main.py --generate --type quotes
```

### Requirements (already in klinik.financial venv)
- `Pillow` — text card rendering
- `ffmpeg` — `/home/asepyudi/bin/ffmpeg`

---

## Usage

```bash
# Generate a random quotes video
python main.py --generate --type quotes

# Generate a hadist video
python main.py --generate --type hadist

# Generate a kisah nabi video
python main.py --generate --type kisah

# List all available content
python main.py --list --type quotes
python main.py --list --type hadist
python main.py --list --type kisah
```

Output videos go to `output/` as `{type}_{timestamp}.mp4`.

---

## Project Structure

```
rafa-story/
├── main.py                  # CLI entrypoint
├── agents/
│   ├── content_generator.py # Load & select content from JSON
│   └── video_maker.py       # Render card + compose video with ffmpeg
├── content/
│   ├── quotes.json          # 22 quotes dari Sahabat Nabi
│   ├── hadist.json          # 22 hadist dengan sumber
│   └── kisah.json           # 11 kisah nabi & sahabat
├── assets/
│   ├── backgrounds/         # Background videos (Pixabay)
│   │   ├── mosque.mp4
│   │   ├── desert_sunset.mp4
│   │   └── stars_night.mp4
│   ├── fonts/
│   │   └── DejaVuSans-Bold.ttf
│   └── music/               # ← Add background music here
│       └── (add .mp3 files)
├── output/                  # Generated videos
└── .env                     # API keys
```

---

## Adding Background Music

Drop `.mp3` files (soft Islamic instrumental — oud, gambus, no vocals) into `assets/music/`:

```bash
cp your_nasheed.mp3 assets/music/
```

The pipeline auto-detects and mixes it at 20% volume. If no music file is present, the video uses silent audio.

Recommended: search YouTube/SoundCloud for "gambus instrumental", "oud instrumental", or "Islamic background music no copyright".

---

## Content Types

| Type | Label | Count |
|------|-------|-------|
| `quotes` | 💬 Kata Sahabat Nabi | 22 |
| `hadist` | 📖 Hadist | 22 |
| `kisah` | 🕌 Kisah Nabi | 11 |

---

## Backgrounds

Downloaded from Pixabay (free license):

| File | Subject | Duration |
|------|---------|----------|
| `mosque.mp4` | Masjid | 20s |
| `desert_sunset.mp4` | Padang pasir sunset | 33s |
| `stars_night.mp4` | Langit malam berbintang | 36s |

Background videos are looped to fill the 45s duration. To add more, drop any `.mp4` into `assets/backgrounds/` and update the mapping in `agents/video_maker.py`.

---

## Environment

```
PIXABAY_API_KEY=...   # For downloading more backgrounds
ANTHROPIC_API_KEY=... # For future AI content generation
```

---

*Built by Dexter 🔪 for @fakhry831*
