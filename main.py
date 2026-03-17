#!/usr/bin/env python3
"""
main.py - rafa-story pipeline CLI
TikTok Islamic storytelling video generator for @fakhry831

Usage:
  python main.py --generate --type quotes
  python main.py --generate --type hadist
  python main.py --generate --type kisah
  python main.py --generate --type quotes --id 5
  python main.py --list --type quotes
"""
import argparse
import os
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "agents"))

from content_generator import get_random_content, load_quotes, load_hadist, load_kisah
from video_maker import make_video

OUTPUT_DIR = os.path.join(BASE_DIR, "output")


def cmd_generate(args):
    content_type = args.type
    print(f"\n🎬 rafa-story — Generating {content_type} video for @fakhry831")
    print("=" * 60)

    # Get content
    content = get_random_content(content_type)

    print(f"\n📋 Content selected:")
    print(f"   Label  : {content['label']}")
    if 'title' in content:
        print(f"   Title  : {content['title']}")
    print(f"   Text   : {content['text'][:80]}{'...' if len(content['text']) > 80 else ''}")
    if content.get('source'):
        print(f"   Source : {content['source']}")
    print()

    # Output filename
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{content_type}_{ts}.mp4"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Generate video
    make_video(content, output_path)

    print(f"\n✅ Done!")
    print(f"📁 Output: {output_path}")
    print(f"📱 Ready to upload to TikTok @fakhry831")
    return output_path


def cmd_list(args):
    content_type = args.type
    print(f"\n📚 Content database: {content_type}")
    print("=" * 60)

    if content_type == "quotes":
        items = load_quotes()
        for item in items:
            print(f"  [{item['id']:2d}] {item['sahabat']}: {item['quote'][:60]}...")
    elif content_type == "hadist":
        items = load_hadist()
        for item in items:
            print(f"  [{item['id']:2d}] ({item['sumber']}): {item['teks'][:60]}...")
    elif content_type == "kisah":
        items = load_kisah()
        for item in items:
            print(f"  [{item['id']:2d}] {item['judul']}: {item['kisah'][:60]}...")
    else:
        print(f"Unknown type: {content_type}")
        sys.exit(1)

    print(f"\nTotal: {len(items)} items")


def main():
    parser = argparse.ArgumentParser(
        description="rafa-story — Islamic TikTok video pipeline for @fakhry831",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --generate --type quotes
  python main.py --generate --type hadist
  python main.py --generate --type kisah
  python main.py --list --type quotes
        """
    )

    parser.add_argument(
        "--generate", action="store_true",
        help="Generate a video"
    )
    parser.add_argument(
        "--list", action="store_true",
        help="List available content"
    )
    parser.add_argument(
        "--type",
        choices=["quotes", "hadist", "kisah"],
        default="quotes",
        help="Content type (default: quotes)"
    )
    parser.add_argument(
        "--id", type=int, default=None,
        help="Specific content ID (optional, random if not set)"
    )

    args = parser.parse_args()

    if args.generate:
        cmd_generate(args)
    elif args.list:
        cmd_list(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
