"""
detect_players.py
-----------------
Uses gemma4:26b via Ollama to detect American football players in pre-snap
images and draws bounding boxes around them.

Output images are saved to  results/gemma4_26b_bboxes/
"""

import base64
import json
import re
import sys
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

# ── Config ────────────────────────────────────────────────────────────────────
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL      = "gemma4:26b"

ROOT       = Path(__file__).parent
IMAGE_DIR  = ROOT / "Testset" / "Presnap_Images"
OUT_DIR    = ROOT / "results" / "gemma4_26b_bboxes"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BOX_COLOR   = (255, 50, 50)   # red
TEXT_COLOR  = (255, 255, 255)
LINE_WIDTH  = 3

PROMPT = """\
You are a sports-vision assistant. The image shows an American football field just before the snap.

Detect every visible player on the field (both teams, all positions). \
Return ONLY a JSON array — no markdown fences, no explanation. \
Each element must have:
  "label"  : always the string "player"
  "box_2d" : [y1, x1, y2, x2]  coordinates in the range [0, 1000]

Example:
[
  {"label": "player", "box_2d": [420, 180, 550, 230]},
  {"label": "player", "box_2d": [390, 310, 510, 360]}
]
"""

# ── Helpers ───────────────────────────────────────────────────────────────────

def encode_image(path: Path) -> str:
    """Return base64-encoded JPEG bytes for the given image file."""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def query_model(image_path: Path) -> str:
    """Send image to gemma4:26b and return the raw text response."""
    b64 = encode_image(image_path)
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": PROMPT,
                "images": [b64],
            }
        ],
        "stream": False,
        "options": {"temperature": 0.1},
    }
    resp = requests.post(OLLAMA_URL, json=payload, timeout=600)
    resp.raise_for_status()
    return resp.json()["message"]["content"]


def parse_boxes(text: str) -> list[dict]:
    """Extract a JSON array of bounding boxes from model output.

    Gemma 4 returns coordinates as ``box_2d: [y1, x1, y2, x2]`` in the
    range [0, 1000].  We normalise to [0, 1] and convert to [x1, y1, x2, y2].
    """
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        return []
    try:
        raw = json.loads(match.group())
    except json.JSONDecodeError:
        return []

    valid = []
    for b in raw:
        # Accept both "box_2d" (Gemma native) and "bbox" (fallback)
        coords = b.get("box_2d") or b.get("bbox", [])
        if len(coords) != 4:
            continue
        if not all(isinstance(v, (int, float)) for v in coords):
            continue

        # Determine coordinate scale: Gemma uses 0-1000; treat >1 values as such
        scale = 1000.0 if max(coords) > 1.0 else 1.0

        # Gemma box_2d order: [y1, x1, y2, x2]
        y1, x1, y2, x2 = [max(0.0, min(scale, float(v))) / scale for v in coords]
        # Ensure correct ordering
        x1, x2 = min(x1, x2), max(x1, x2)
        y1, y2 = min(y1, y2), max(y1, y2)

        valid.append({"label": b.get("label", "player"), "bbox": [x1, y1, x2, y2]})
    return valid


def draw_boxes(image_path: Path, boxes: list[dict]) -> Image.Image:
    """Draw bounding boxes on a PIL image and return the annotated copy."""
    img = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    w, h = img.size

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
    except Exception:
        font = ImageFont.load_default()

    for i, det in enumerate(boxes, 1):
        x1, y1, x2, y2 = det["bbox"]
        px1, py1 = int(x1 * w), int(y1 * h)
        px2, py2 = int(x2 * w), int(y2 * h)

        draw.rectangle([px1, py1, px2, py2], outline=BOX_COLOR, width=LINE_WIDTH)

        label = f"#{i}"
        bbox_text = draw.textbbox((px1, py1 - 16), label, font=font)
        draw.rectangle(bbox_text, fill=BOX_COLOR)
        draw.text((px1, py1 - 16), label, fill=TEXT_COLOR, font=font)

    return img


# ── Main ──────────────────────────────────────────────────────────────────────

def process_image(image_path: Path) -> None:
    out_path = OUT_DIR / image_path.name
    print(f"  Querying model...", end=" ", flush=True)
    raw = query_model(image_path)
    boxes = parse_boxes(raw)
    print(f"{len(boxes)} players detected")

    annotated = draw_boxes(image_path, boxes)
    annotated.save(out_path)

    # Save raw response alongside
    (OUT_DIR / (image_path.stem + "_response.json")).write_text(
        json.dumps({"raw": raw, "boxes": boxes}, indent=2), encoding="utf-8"
    )


IMAGE_NAME = "Game4_Wide---Clip-037_t1.jpg"


def main():
    img_path = IMAGE_DIR / IMAGE_NAME
    if not img_path.exists():
        print(f"Image not found: {img_path}")
        sys.exit(1)

    print(f"Model  : {MODEL}")
    print(f"Image  : {img_path.name}")
    print(f"Output : {OUT_DIR}\n")

    try:
        process_image(img_path)
        print(f"\nDone. Annotated image saved to {OUT_DIR / img_path.name}")
    except Exception as e:
        print(f"ERROR: {e}")


if __name__ == "__main__":
    main()
