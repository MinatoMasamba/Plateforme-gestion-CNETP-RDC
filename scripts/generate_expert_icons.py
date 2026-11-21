"""Décliner le logo exact de l'en-tête, sans le redessiner."""
from pathlib import Path

from PIL import Image, ImageOps

root = Path(__file__).resolve().parents[1] / 'flutter_app'
source = Image.open(root / 'assets/img/logo-cnetp.png').convert('RGBA')


def icon(size):
    fitted = ImageOps.contain(source, (size, size), Image.Resampling.LANCZOS)
    canvas = Image.new('RGBA', (size, size), 'white')
    canvas.alpha_composite(fitted, ((size - fitted.width) // 2, (size - fitted.height) // 2))
    return canvas


for density, size in [('mdpi', 48), ('hdpi', 72), ('xhdpi', 96), ('xxhdpi', 144), ('xxxhdpi', 192)]:
    target = root / f'android/app/src/main/res/mipmap-{density}/ic_launcher.png'
    target.parent.mkdir(parents=True, exist_ok=True)
    icon(size).save(target)
icon(256).save(root / 'windows/runner/resources/app_icon.ico', sizes=[(size, size) for size in (16, 24, 32, 48, 64, 128, 256)])
