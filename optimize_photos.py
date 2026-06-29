from __future__ import annotations

from pathlib import Path

try:
    from PIL import Image
except ImportError as exc:
    raise SystemExit(
        "Pillow is not installed. Run this first:\n\n"
        "python -m pip install Pillow\n"
    ) from exc


SOURCE_DIR = Path("webapp/photos")
OUTPUT_DIR = Path("webapp/photos_optimized")
MAX_WIDTH = 1100
QUALITY = 78


def optimize_image(source: Path, output: Path) -> None:
    image = Image.open(source)
    image = image.convert("RGB")

    if image.width > MAX_WIDTH:
        ratio = MAX_WIDTH / image.width
        new_size = (MAX_WIDTH, int(image.height * ratio))
        image = image.resize(new_size, Image.Resampling.LANCZOS)

    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, "JPEG", quality=QUALITY, optimize=True, progressive=True)


def main() -> None:
    if not SOURCE_DIR.exists():
        raise SystemExit(f"Folder not found: {SOURCE_DIR}")

    files = sorted(SOURCE_DIR.glob("*.png")) + sorted(SOURCE_DIR.glob("*.jpg")) + sorted(SOURCE_DIR.glob("*.jpeg"))
    if not files:
        raise SystemExit(f"No images found in {SOURCE_DIR}")

    print(f"Optimizing {len(files)} image(s)...")
    for source in files:
        output = OUTPUT_DIR / f"{source.stem}.jpg"
        before = source.stat().st_size
        optimize_image(source, output)
        after = output.stat().st_size
        saved = 100 - round(after / before * 100, 1)
        print(f"{source.name} -> {output.name}: {before // 1024} KB -> {after // 1024} KB, saved {saved}%")

    print("\nDone. Upload webapp/photos_optimized to hosting too.")


if __name__ == "__main__":
    main()
