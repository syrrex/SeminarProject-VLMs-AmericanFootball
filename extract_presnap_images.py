import csv
import os
import subprocess
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent
MANIFEST = SCRIPT_DIR / "Testset" / "manifest.csv"
OUTPUT_DIR = SCRIPT_DIR / "Testset" / "Presnap_Images"

OUTPUT_DIR.mkdir(exist_ok=True)

with open(MANIFEST, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

errors = []

for row in rows:
    rel_path = row["PATH"].lstrip("/")  # e.g. Testset/Game1/Wide - Clip 004.mp4
    video_path = SCRIPT_DIR / rel_path
    start_sec = int(row["START"])

    if not video_path.exists():
        print(f"[MISSING] {video_path}")
        errors.append(str(video_path))
        continue

    # Build output filename: Game1_Wide-Clip004_t14.jpg
    game = video_path.parent.name           # e.g. Game1
    stem = video_path.stem.replace(" ", "-")  # e.g. Wide-Clip-004
    out_name = f"{game}_{stem}_t{start_sec}.jpg"
    out_path = OUTPUT_DIR / out_name

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_sec),
        "-i", str(video_path),
        "-frames:v", "1",
        "-q:v", "2",
        str(out_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ERROR] {video_path.name}: {result.stderr.splitlines()[-1]}")
        errors.append(str(video_path))
    else:
        print(f"[OK] {out_name}")

print(f"\nDone. {len(rows) - len(errors)}/{len(rows)} screenshots saved to {OUTPUT_DIR}")
if errors:
    print("Failed:")
    for e in errors:
        print(f"  {e}")
