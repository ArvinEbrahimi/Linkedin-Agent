"""Generate minimal LinkAid extension icons (blue square with L)."""

from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    raise SystemExit("Install Pillow: pip install pillow") from None

OUT = Path(__file__).resolve().parent.parent / "extension" / "icons"
COLOR = (10, 102, 194)


def make_icon(size: int, path: Path) -> None:
    img = Image.new("RGB", (size, size), COLOR)
    draw = ImageDraw.Draw(img)
    margin = size // 4
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=size // 8,
        fill=(255, 255, 255),
    )
    try:
        font = ImageFont.truetype("arial.ttf", size // 2)
    except OSError:
        font = ImageFont.load_default()
    draw.text((size * 0.32, size * 0.22), "L", fill=COLOR, font=font)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


if __name__ == "__main__":
    for s in (16, 48, 128):
        make_icon(s, OUT / f"icon{s}.png")
    print(f"Wrote icons to {OUT}")
