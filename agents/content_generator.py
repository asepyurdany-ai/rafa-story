"""
content_generator.py - Load and select content from JSON databases
"""
import json
import random
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT_DIR = os.path.join(BASE_DIR, "content")


def load_quotes():
    path = os.path.join(CONTENT_DIR, "quotes.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_hadist():
    path = os.path.join(CONTENT_DIR, "hadist.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_kisah():
    path = os.path.join(CONTENT_DIR, "kisah.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_random_content(content_type: str) -> dict:
    """
    Get a random content item by type.
    content_type: 'quotes', 'hadist', 'kisah'
    Returns a dict with keys: label, text, source (optional), author (optional)
    """
    print(f"[ContentGenerator] Loading content type: {content_type}")

    if content_type == "quotes":
        items = load_quotes()
        item = random.choice(items)
        return {
            "type": "quotes",
            "label": item["label"],
            "text": item["quote"],
            "author": item["sahabat"],
            "source": f"— {item['sahabat']}",
        }
    elif content_type == "hadist":
        items = load_hadist()
        item = random.choice(items)
        return {
            "type": "hadist",
            "label": item["label"],
            "text": item["teks"],
            "author": item["rawi"],
            "source": item["sumber"],
        }
    elif content_type == "kisah":
        items = load_kisah()
        item = random.choice(items)
        return {
            "type": "kisah",
            "label": item["label"],
            "title": item["judul"],
            "text": item["kisah"],
            "source": "",
        }
    else:
        raise ValueError(f"Unknown content type: {content_type}")


def get_content_by_id(content_type: str, content_id: int) -> dict:
    """Get specific content by ID."""
    if content_type == "quotes":
        items = load_quotes()
    elif content_type == "hadist":
        items = load_hadist()
    elif content_type == "kisah":
        items = load_kisah()
    else:
        raise ValueError(f"Unknown content type: {content_type}")

    for item in items:
        if item["id"] == content_id:
            return get_random_content.__wrapped__(content_type, item) if False else item
    raise ValueError(f"Content ID {content_id} not found in {content_type}")


if __name__ == "__main__":
    for ctype in ["quotes", "hadist", "kisah"]:
        content = get_random_content(ctype)
        print(f"\n[{ctype.upper()}]")
        print(f"Label: {content['label']}")
        print(f"Text: {content['text'][:100]}...")
