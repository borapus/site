"""Generate deterministic responsive WebP assets. Requires Pillow; no build-time service."""
from pathlib import Path
from PIL import Image, ImageOps
from concurrent.futures import ThreadPoolExecutor
import hashlib, json

root = Path(__file__).resolve().parents[1]
public = root / 'public'
text = (root/'src/data/uploadedProjects.ts').read_text(encoding='utf-8')
projects = json.loads(text.split(' = ', 1)[1].rstrip().removesuffix(';'))
paths = {p for record in projects for p in [record['cover'], *record['gallery']]}
covers = {record['cover'] for record in projects}
covers.update(['/images/projects/gu-house.jpg', '/images/projects/uc-house.jpg'])
paths.update(['/images/projects/gu-house.jpg', '/images/projects/uc-house.jpg', '/images/hero.jpg', '/images/studio-nostalgic.png', '/logo-pusco.png'])
dest = public/'images/optimized'
dest.mkdir(parents=True, exist_ok=True)
def prepare(path):
    source = public/path.lstrip('/')
    logo = path == '/logo-pusco.png'
    hero = path == '/images/hero.jpg'
    quality = 85 if logo else 72 if hero else 82
    specification = f'webp-v2-q{quality}-logo' if logo else f'webp-v2-q{quality}-hero' if hero else 'webp-v1-q82'
    digest = hashlib.sha256(source.read_bytes() + specification.encode()).hexdigest()[:16]
    with Image.open(source) as original:
        im = ImageOps.exif_transpose(original).convert('RGBA' if logo else 'RGB')
        width, height = im.size
        variants = []
        sizes = [340, 680] if logo else [640, 960, 1280, 1920] if hero or path in covers else [640, 1280, 1920]
        for size in sorted({min(width, n) for n in sizes}):
            name = f'{digest}-{size}.webp'
            target = dest/name
            if not target.exists():
                resized = im.resize((size, max(1, round(height*size/width))), Image.Resampling.LANCZOS)
                resized.save(target, 'WEBP', quality=quality, method=4)
            variants.append({'src': f'/images/optimized/{name}', 'width': size})
    return path, {'width': width, 'height': height, 'variants': variants}
with ThreadPoolExecutor(max_workers=4) as pool:
    manifest = dict(pool.map(prepare, sorted(paths)))
(root/'src/data/imageManifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(f'Prepared {len(manifest)} image records and {sum(len(x["variants"]) for x in manifest.values())} responsive variants.')
