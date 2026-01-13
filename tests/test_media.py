"""
Testes do Pipeline de Mídia - Igreja São Sebastião

Testa:
- Validação de arquivos (MIME type, tamanho)
- Processamento de imagens (resize, WebP)
- Geração de variantes
- Limpeza de órfãos
"""

import pytest
import sys
import os
import io
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image
from werkzeug.datastructures import FileStorage


class TestMediaValidation:
    """Testes de validação de mídia"""

    @pytest.fixture
    def temp_upload_folder(self):
        """Cria pasta temporária para uploads"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def pipeline(self, temp_upload_folder):
        """Cria instância do pipeline"""
        from core.media import MediaPipeline
        return MediaPipeline(upload_folder=temp_upload_folder)

    def _create_test_image(self, width=100, height=100, format='PNG') -> io.BytesIO:
        """Cria imagem de teste em memória"""
        img = Image.new('RGB', (width, height), color='red')
        buffer = io.BytesIO()
        img.save(buffer, format=format)
        buffer.seek(0)
        return buffer

    def _create_file_storage(self, buffer: io.BytesIO, filename: str) -> FileStorage:
        """Cria FileStorage a partir de buffer"""
        return FileStorage(
            stream=buffer,
            filename=filename,
            content_type='image/png'
        )

    def test_valid_png_accepted(self, pipeline):
        """Prova que PNG válido é aceito"""
        buffer = self._create_test_image(format='PNG')
        file = self._create_file_storage(buffer, 'test.png')

        is_valid, error = pipeline.validate_file(file)

        assert is_valid is True
        assert error is None

    def test_valid_jpeg_accepted(self, pipeline):
        """Prova que JPEG válido é aceito"""
        buffer = self._create_test_image(format='JPEG')
        file = self._create_file_storage(buffer, 'test.jpg')

        is_valid, error = pipeline.validate_file(file)

        assert is_valid is True
        assert error is None

    def test_empty_file_rejected(self, pipeline):
        """Prova que arquivo vazio é rejeitado"""
        buffer = io.BytesIO(b'')
        file = self._create_file_storage(buffer, 'empty.png')

        is_valid, error = pipeline.validate_file(file)

        assert is_valid is False
        assert 'vazio' in error.lower()

    def test_invalid_mime_rejected(self, pipeline):
        """Prova que arquivos com MIME inválido são rejeitados"""
        # Criar arquivo de texto fingindo ser imagem
        buffer = io.BytesIO(b'This is not an image')
        file = FileStorage(stream=buffer, filename='fake.png')

        is_valid, error = pipeline.validate_file(file)

        assert is_valid is False
        assert 'não permitido' in error.lower()

    def test_oversized_file_rejected(self, pipeline):
        """Prova que arquivo muito grande é rejeitado"""
        # Temporariamente reduzir limite para teste
        original_limit = pipeline.MAX_FILE_SIZE
        pipeline.MAX_FILE_SIZE = 1024  # 1KB

        # Criar imagem grande
        buffer = self._create_test_image(width=1000, height=1000)
        file = self._create_file_storage(buffer, 'large.png')

        is_valid, error = pipeline.validate_file(file)

        # Restaurar limite
        pipeline.MAX_FILE_SIZE = original_limit

        assert is_valid is False
        assert 'grande' in error.lower()


class TestImageProcessing:
    """Testes de processamento de imagem"""

    @pytest.fixture
    def temp_upload_folder(self):
        """Cria pasta temporária para uploads"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def pipeline(self, temp_upload_folder):
        """Cria instância do pipeline"""
        from core.media import MediaPipeline
        return MediaPipeline(upload_folder=temp_upload_folder)

    def _create_test_image(self, width=800, height=600, format='PNG') -> io.BytesIO:
        """Cria imagem de teste em memória"""
        img = Image.new('RGB', (width, height), color='blue')
        buffer = io.BytesIO()
        img.save(buffer, format=format)
        buffer.seek(0)
        return buffer

    def _create_file_storage(self, buffer: io.BytesIO, filename: str) -> FileStorage:
        """Cria FileStorage a partir de buffer"""
        return FileStorage(
            stream=buffer,
            filename=filename,
            content_type='image/png'
        )

    def test_process_creates_all_variants(self, pipeline):
        """Prova que processamento cria todas as variantes"""
        buffer = self._create_test_image(width=1500, height=1000)
        file = self._create_file_storage(buffer, 'test.png')

        result = pipeline.process(file, convert_to_webp=False)

        # Deve ter 4 variantes: original, thumb, medium, large
        assert len(result.variants) == 4
        assert 'original' in result.variants
        assert 'thumb' in result.variants
        assert 'medium' in result.variants
        assert 'large' in result.variants

    def test_thumb_size_correct(self, pipeline):
        """Prova que thumbnail tem tamanho correto"""
        buffer = self._create_test_image(width=1500, height=1000)
        file = self._create_file_storage(buffer, 'test.png')

        result = pipeline.process(file, convert_to_webp=False)

        thumb = result.variants['thumb']
        assert thumb.width <= 300
        assert thumb.height <= 300

    def test_medium_size_correct(self, pipeline):
        """Prova que versão medium tem tamanho correto"""
        buffer = self._create_test_image(width=1500, height=1000)
        file = self._create_file_storage(buffer, 'test.png')

        result = pipeline.process(file, convert_to_webp=False)

        medium = result.variants['medium']
        assert medium.width <= 800
        assert medium.height <= 800

    def test_webp_conversion(self, pipeline):
        """Prova que conversão para WebP funciona"""
        buffer = self._create_test_image(width=500, height=500)
        file = self._create_file_storage(buffer, 'test.png')

        result = pipeline.process(file, convert_to_webp=True)

        # URL deve terminar em .webp (exceto original)
        assert result.primary_url.endswith('.webp')
        assert result.thumb_url.endswith('.webp')

    def test_aspect_ratio_preserved(self, pipeline):
        """Prova que proporção é mantida no resize"""
        # Imagem 2:1
        buffer = self._create_test_image(width=1000, height=500)
        file = self._create_file_storage(buffer, 'test.png')

        result = pipeline.process(file, convert_to_webp=False)

        medium = result.variants['medium']
        # Proporção deve ser aproximadamente 2:1
        ratio = medium.width / medium.height
        assert 1.9 < ratio < 2.1

    def test_small_image_not_upscaled(self, pipeline):
        """Prova que imagens pequenas não são aumentadas"""
        # Imagem menor que thumb
        buffer = self._create_test_image(width=100, height=100)
        file = self._create_file_storage(buffer, 'test.png')

        result = pipeline.process(file, convert_to_webp=False)

        # Todas as variantes devem manter 100x100
        for size in ['thumb', 'medium', 'large']:
            variant = result.variants[size]
            assert variant.width == 100
            assert variant.height == 100


class TestFileManagement:
    """Testes de gerenciamento de arquivos"""

    @pytest.fixture
    def temp_upload_folder(self):
        """Cria pasta temporária para uploads"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def pipeline(self, temp_upload_folder):
        """Cria instância do pipeline"""
        from core.media import MediaPipeline
        return MediaPipeline(upload_folder=temp_upload_folder)

    def _create_test_image(self, width=100, height=100) -> io.BytesIO:
        """Cria imagem de teste"""
        img = Image.new('RGB', (width, height), color='green')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer

    def test_delete_removes_all_variants(self, pipeline):
        """Prova que delete remove todas as variantes"""
        buffer = self._create_test_image()
        file = FileStorage(stream=buffer, filename='test.png')

        result = pipeline.process(file, convert_to_webp=False)
        stored_name = result.stored_name

        # Verificar que arquivos existem
        for variant in result.variants.values():
            assert Path(variant.path).exists()

        # Deletar
        deleted = pipeline.delete_image(stored_name)

        # Deve ter deletado 4 arquivos
        assert deleted == 4

        # Verificar que arquivos não existem mais
        for variant in result.variants.values():
            assert not Path(variant.path).exists()

    def test_get_stats_returns_info(self, pipeline):
        """Prova que estatísticas retornam informações corretas"""
        # Criar algumas imagens
        for i in range(3):
            buffer = self._create_test_image()
            file = FileStorage(stream=buffer, filename=f'test{i}.png')
            pipeline.process(file, convert_to_webp=False)

        stats = pipeline.get_stats()

        assert stats['total_files'] == 12  # 3 imagens x 4 variantes
        assert 'by_size' in stats
        assert 'thumb' in stats['by_size']
        assert stats['by_size']['thumb']['files'] == 3


class TestMimeDetection:
    """Testes de detecção de MIME type"""

    @pytest.fixture
    def temp_upload_folder(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def pipeline(self, temp_upload_folder):
        from core.media import MediaPipeline
        return MediaPipeline(upload_folder=temp_upload_folder)

    def test_detect_jpeg_magic_bytes(self, pipeline):
        """Prova que JPEG é detectado pelos magic bytes"""
        img = Image.new('RGB', (10, 10))
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG')
        buffer.seek(0)

        file = FileStorage(stream=buffer, filename='test.jpg')
        mime = pipeline._detect_mime_type(file)

        assert mime == 'image/jpeg'

    def test_detect_png_magic_bytes(self, pipeline):
        """Prova que PNG é detectado pelos magic bytes"""
        img = Image.new('RGB', (10, 10))
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        file = FileStorage(stream=buffer, filename='test.png')
        mime = pipeline._detect_mime_type(file)

        assert mime == 'image/png'

    def test_detect_gif_magic_bytes(self, pipeline):
        """Prova que GIF é detectado pelos magic bytes"""
        img = Image.new('P', (10, 10))
        buffer = io.BytesIO()
        img.save(buffer, format='GIF')
        buffer.seek(0)

        file = FileStorage(stream=buffer, filename='test.gif')
        mime = pipeline._detect_mime_type(file)

        assert mime == 'image/gif'


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
