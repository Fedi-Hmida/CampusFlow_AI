"""CF-113 / CF-208d — derive the degraded T4 photos from Ines's sharp images, and draw the unrelated image.

  T4-01_convocation_ds14_5ds6.png  → T4-09_convocation_ds14_blurry.jpg   (dim light + horizontal motion blur + slight angle)
  T4-06_emploi_du_temps_2a7.jpg    → T4-10_emploi_du_temps_rotated.jpg   (rotated 90° clockwise)
  (drawn)                          → T4-11_unrelated_menu.png            (cafeteria menu board, nothing academic)
The sources stay tests of their own. Deterministic: re-running gives the same images.
Run: .venv/Scripts/python scripts/testsets/degrade_t4.py
"""
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
P = ROOT / "eval/testsets/T4_photos"
JOBS = {"T4-01_convocation_ds14_5ds6.png": "T4-09_convocation_ds14_blurry.jpg",
        "T4-06_emploi_du_temps_2a7.jpg": "T4-10_emploi_du_temps_rotated.jpg"}
UNRELATED = "T4-11_unrelated_menu.png"


def motion_blur(img: Image.Image, length: int = 9) -> Image.Image:
    """Average of horizontally shifted copies = linear motion blur (Pillow has no motion-blur filter)."""
    acc = img.copy()
    for i in range(1, length):
        shifted = ImageChops.offset(img, i - length // 2, 0)
        acc = Image.blend(acc, shifted, 1.0 / (i + 1))
    return acc


def blurry(img: Image.Image) -> Image.Image:
    img = img.convert("RGB")
    w = img.width
    img = motion_blur(img, length=max(9, w // 80))            # scales with resolution: ~16 px on a 1280 px image
    img = img.filter(ImageFilter.GaussianBlur(radius=max(1.5, w / 700)))
    img = ImageEnhance.Brightness(img).enhance(0.55)          # dim light
    img = ImageEnhance.Contrast(img).enhance(0.75)
    return img.rotate(4, resample=Image.BICUBIC, expand=True, fillcolor=(20, 20, 20))  # slight angle


def menu_board() -> Image.Image:
    """A chalkboard cafeteria menu: the 'unrelated photo' case (no school data at all). ASCII text: Pillow's
    built-in font has no accents, and a system font would make the image machine-dependent."""
    img = Image.new("RGB", (1024, 1280), (38, 58, 48))
    d = ImageDraw.Draw(img)
    d.rectangle([24, 24, 999, 1255], outline=(140, 100, 60), width=28)
    big, mid, small = (ImageFont.load_default(size=s) for s in (78, 50, 30))
    d.text((512, 170), "MENU DU JOUR", font=big, fill=(240, 240, 230), anchor="mm")
    d.line([200, 240, 824, 240], fill=(240, 240, 230), width=4)
    for i, dish in enumerate(["Couscous aux legumes", "Salade mechouia", "Lablabi", "Yaourt ou fruit", "The a la menthe"]):
        d.text((512, 380 + i * 140), dish, font=mid, fill=(235, 235, 220), anchor="mm")
    d.text((512, 1180), "Cafeteria - image de test, projet CampusFlow AI", font=small, fill=(200, 200, 190), anchor="mm")
    return img


def main() -> None:
    missing = [s for s in JOBS if not (P / s).exists()]
    if missing:
        sys.exit(f"missing source images in eval/testsets/T4_photos/: {missing}")
    for src, dst in JOBS.items():
        img = Image.open(P / src)
        out = blurry(img) if "blurry" in dst else img.convert("RGB").rotate(-90, expand=True)  # -90 = clockwise
        out.save(P / dst, quality=88)
        print(f"{src} ({img.width}x{img.height}) → {dst} ({out.width}x{out.height})")
    menu_board().save(P / UNRELATED)
    print(f"drawn → {UNRELATED}")


if __name__ == "__main__":
    main()
