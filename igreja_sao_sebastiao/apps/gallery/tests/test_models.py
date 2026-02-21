import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.gallery.models import GalleryImage


def _create_test_image(width=100, height=100, fmt="JPEG"):
    """Create an in-memory test image."""
    img = Image.new("RGB", (width, height), color="red")
    buffer = io.BytesIO()
    img.save(buffer, format=fmt)
    buffer.seek(0)
    ext = "jpg" if fmt == "JPEG" else fmt.lower()
    return SimpleUploadedFile(f"test.{ext}", buffer.read(), content_type=f"image/{ext}")


@pytest.mark.django_db
class TestGalleryImageModel:
    def test_create_image(self):
        img_file = _create_test_image()
        gallery = GalleryImage.objects.create(
            titulo="Foto teste",
            descricao="Descrição",
            categoria="igreja",
            imagem=img_file,
        )
        assert str(gallery) == "Foto teste"
        assert gallery.ativo is True
        assert gallery.imagem is not None

    def test_default_category(self):
        img_file = _create_test_image()
        gallery = GalleryImage.objects.create(
            titulo="Foto",
            imagem=img_file,
        )
        assert gallery.categoria == "outros"

    def test_ordering(self):
        for i in range(3):
            GalleryImage.objects.create(
                titulo=f"Foto {i}",
                imagem=_create_test_image(),
            )
        fotos = list(GalleryImage.objects.values_list("titulo", flat=True))
        assert fotos[0] == "Foto 2"  # Most recent first
