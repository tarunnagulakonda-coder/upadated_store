"""Product image upload + optimization (Flask, no Django).

Single place that knows how product images are validated, resized,
compressed and stored. Callers store only the returned relative path
(e.g. "uploads/products/1700000000_apple.webp") in Product.image_url —
never binary data in PostgreSQL.

Current backend: local static folder (works locally + on Render for
testing). To move to Cloudinary/S3 later, replace _store_bytes() with an
uploader that returns a remote URL; all callers/templates already accept
absolute http(s) URLs via resolve_product_image_src().
"""
import io
import os
import time

from flask import current_app
from werkzeug.utils import secure_filename

ALLOWED_PRODUCT_EXTS = {'jpg', 'jpeg', 'png', 'webp'}
MAX_PRODUCT_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB original
MAX_PRODUCT_DIM = (800, 800)  # width x height, aspect preserved
PRODUCT_WEBP_QUALITY = 80
PRODUCT_JPEG_QUALITY = 80


def product_upload_dir():
    upload_dir = os.path.join(current_app.static_folder, 'uploads', 'products')
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


def resolve_product_image_src(image_url):
    """Map a Product.image_url value to a template-ready src.

    Accepts: None, absolute http(s) URL (Cloudinary-ready), "uploads/..."
    path, or legacy bare filename ("apple.jpg" -> "uploads/<name>").
    """
    if not image_url:
        return None
    value = image_url.strip()
    if not value:
        return None
    if value.startswith(('http://', 'https://', 'data:')):
        return value
    normalized = value.replace('\\', '/').lstrip('/')
    if normalized.startswith('uploads/'):
        return normalized
    # Legacy rows stored only the filename.
    return f'uploads/{normalized}'


def _store_bytes(data: bytes, filename: str) -> str:
    """Persist optimized bytes; returns path relative to static folder."""
    upload_dir = product_upload_dir()
    with open(os.path.join(upload_dir, filename), 'wb') as fh:
        fh.write(data)
    return f'uploads/products/{filename}'


def save_product_image(file):
    """Validate, resize and compress an uploaded product image.

    Returns the relative path to store in Product.image_url, or None when
    no file was provided (image is optional). Raises ValueError with a
    user-facing message for invalid files.
    """
    if not file or not getattr(file, 'filename', ''):
        return None
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_PRODUCT_EXTS:
        raise ValueError('Unsupported image type. Please upload JPG, PNG or WebP.')
    raw = file.read()
    # file.read() consumes the stream; restore for any later use.
    try:
        file.seek(0)
    except Exception:
        pass
    if not raw:
        raise ValueError('Empty image file. Please choose another image.')
    if len(raw) > MAX_PRODUCT_UPLOAD_BYTES:
        raise ValueError('Image is too large (max 5 MB). Please choose a smaller image.')

    try:
        from PIL import Image
    except ImportError as exc:
        raise ValueError('Image processing is unavailable on the server.') from exc

    try:
        img = Image.open(io.BytesIO(raw))
        img.verify()  # rejects non-images / corrupt files
        img = Image.open(io.BytesIO(raw))  # verify() closes it; reopen
    except Exception as exc:
        raise ValueError('Invalid image file. Please upload JPG, PNG or WebP.') from exc

    # Normalize modes: drop alpha for JPEG fallback; WebP keeps alpha.
    has_alpha = img.mode in ('RGBA', 'LA', 'PA', 'P')
    try:
        if img.mode == 'P':
            img = img.convert('RGBA' if 'transparency' in img.info else 'RGB')
        elif img.mode not in ('RGB', 'RGBA'):
            img = img.convert('RGBA' if has_alpha else 'RGB')
    except Exception as exc:
        raise ValueError('Could not read this image. Please try another file.') from exc

    # Resize BEFORE storing: thumbnail preserves aspect ratio, never upscales
    # small images, uses high-quality Lanczos downsampling.
    try:
        img.thumbnail(MAX_PRODUCT_DIM, Image.LANCZOS)
    except Exception as exc:
        raise ValueError('Could not process this image. Please try another file.') from exc

    base = secure_filename(os.path.splitext(file.filename)[0] or 'product')[:60] or 'product'
    stamp = int(time.time() * 1000)

    # Prefer WebP (quality 80, method 6). Fall back to JPEG (quality 80,
    # optimized) when WebP encode is unavailable (e.g. minimal Pillow build).
    for attempt in ('webp', 'jpeg'):
        try:
            buf = io.BytesIO()
            if attempt == 'webp':
                save_img = img
                # WebP supports alpha; JPEG does not.
                save_img.save(buf, format='WEBP', quality=PRODUCT_WEBP_QUALITY,
                              method=6, lossless=False)
                filename = f'{stamp}_{base}.webp'
            else:
                save_img = img.convert('RGB') if img.mode in ('RGBA', 'LA', 'PA', 'P') else img
                filename = f'{stamp}_{base}.jpg'
                save_img.save(buf, format='JPEG', quality=PRODUCT_JPEG_QUALITY,
                              optimize=True, progressive=True)
            return _store_bytes(buf.getvalue(), filename)
        except Exception:
            if attempt == 'jpeg':
                raise ValueError('Could not process this image. Please try another file.')
            continue
    raise ValueError('Could not process this image. Please try another file.')
