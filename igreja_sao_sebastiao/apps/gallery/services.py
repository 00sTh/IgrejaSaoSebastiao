"""
Image processing service - port of core/media.py from Flask.
Handles resize, WebP conversion, and EXIF orientation correction.
"""

import contextlib
import uuid
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image, ImageOps


def process_gallery_image(gallery_image):
    """
    Generate thumb, medium, and large variants for a GalleryImage instance.
    Called automatically on save() when the image is new.
    """
    if not gallery_image.imagem:
        return

    try:
        img = Image.open(gallery_image.imagem)
    except Exception:
        return

    # Fix EXIF orientation
    with contextlib.suppress(Exception):
        img = ImageOps.exif_transpose(img)

    # Convert palette/CMYK images to RGB(A)
    if img.mode in ("P", "CMYK"):
        img = img.convert("RGBA")

    sizes = settings.IMAGE_SIZES
    unique_id = uuid.uuid4().hex[:8]
    base_name = Path(gallery_image.imagem.name).stem

    variants = {}
    for size_name, config in sizes.items():
        resized = _resize(img.copy(), config["max_width"], config["max_height"])
        buffer = BytesIO()

        # Save as WebP for better compression
        save_img = resized.convert("RGB") if resized.mode == "RGBA" else resized
        save_img.save(buffer, format="WEBP", quality=config["quality"], method=4)
        buffer.seek(0)

        filename = f"{base_name}_{unique_id}_{size_name}.webp"
        variants[size_name] = ContentFile(buffer.read(), name=filename)

    # Save variants without triggering save() again
    update_fields = []
    if variants.get("thumb"):
        gallery_image.imagem_thumb = variants["thumb"]
        update_fields.append("imagem_thumb")
    if variants.get("medium"):
        gallery_image.imagem_medium = variants["medium"]
        update_fields.append("imagem_medium")
    if variants.get("large"):
        gallery_image.imagem_large = variants["large"]
        update_fields.append("imagem_large")

    if update_fields:
        # Use update_fields to avoid recursive save
        type(gallery_image).objects.filter(pk=gallery_image.pk).update(
            **{f: getattr(gallery_image, f) for f in update_fields}
        )
        # Actually save the files
        for field_name in update_fields:
            field = getattr(gallery_image, field_name)
            if field and hasattr(field, "name"):
                field.save(field.name, variants[field_name.replace("imagem_", "")], save=False)
        type(gallery_image).objects.filter(pk=gallery_image.pk).update(
            imagem_thumb=gallery_image.imagem_thumb,
            imagem_medium=gallery_image.imagem_medium,
            imagem_large=gallery_image.imagem_large,
        )

    img.close()


def _resize(img, max_width, max_height):
    """Resize keeping aspect ratio using LANCZOS resampling."""
    ratio = min(max_width / img.width, max_height / img.height)
    if ratio < 1:
        new_width = int(img.width * ratio)
        new_height = int(img.height * ratio)
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    return img
