"""
Pipeline de Mídia - Igreja São Sebastião
Sistema completo de upload, processamento e otimização de imagens.
"""

import os
import uuid
import hashlib
import mimetypes
from datetime import datetime
from typing import Dict, List, Optional, Tuple, BinaryIO
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from PIL import Image, ImageOps, ExifTags
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

from middleware.logger import log_request, log_error


class ImageSize(Enum):
    """Tamanhos padrão de imagem"""
    THUMB = "thumb"      # 300px - miniaturas
    MEDIUM = "medium"    # 800px - listagens
    LARGE = "large"      # 1200px - visualização
    ORIGINAL = "original"  # tamanho original


@dataclass
class ImageVariant:
    """Representa uma variante processada da imagem"""
    size: ImageSize
    path: str
    url: str
    width: int
    height: int
    file_size: int


@dataclass
class ProcessedImage:
    """Resultado do processamento de imagem"""
    original_name: str
    stored_name: str
    content_type: str
    variants: Dict[str, ImageVariant]
    primary_url: str  # URL principal (medium)
    thumb_url: str
    created_at: datetime


class MediaValidationError(Exception):
    """Erro de validação de mídia"""
    pass


class MediaPipeline:
    """
    Pipeline de processamento de mídia.

    Responsabilidades:
    - Validação de segurança (MIME type, tamanho)
    - Resize para múltiplos tamanhos
    - Conversão para WebP
    - Otimização de qualidade
    - Remoção de metadados EXIF
    """

    # Configurações padrão
    ALLOWED_MIME_TYPES = {
        'image/jpeg': ['.jpg', '.jpeg'],
        'image/png': ['.png'],
        'image/gif': ['.gif'],
        'image/webp': ['.webp'],
    }

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    # Tamanhos de resize (largura máxima)
    SIZE_CONFIG = {
        ImageSize.THUMB: {"max_width": 300, "max_height": 300, "quality": 80},
        ImageSize.MEDIUM: {"max_width": 800, "max_height": 800, "quality": 85},
        ImageSize.LARGE: {"max_width": 1200, "max_height": 1200, "quality": 90},
    }

    def __init__(self, upload_folder: str, url_prefix: str = "/static/uploads"):
        """
        Inicializa o pipeline.

        Args:
            upload_folder: Pasta base para uploads (ex: "static/uploads")
            url_prefix: Prefixo de URL para servir arquivos
        """
        self.upload_folder = Path(upload_folder)
        self.url_prefix = url_prefix
        self._ensure_folders()

    def _ensure_folders(self):
        """Cria estrutura de pastas necessária"""
        for size in ImageSize:
            folder = self.upload_folder / size.value
            folder.mkdir(parents=True, exist_ok=True)

    # ==================== VALIDAÇÃO ====================

    def validate_file(self, file: FileStorage) -> Tuple[bool, Optional[str]]:
        """
        Valida arquivo antes do processamento.

        Verifica:
        - Se arquivo foi enviado
        - Tamanho máximo
        - MIME type real (não apenas extensão)

        Returns:
            (is_valid: bool, error_message: Optional[str])
        """
        # Verificar se arquivo existe
        if not file or not file.filename:
            return False, "Nenhum arquivo enviado"

        # Verificar tamanho
        file.seek(0, 2)  # Vai para o final
        size = file.tell()
        file.seek(0)  # Volta para o início

        if size > self.MAX_FILE_SIZE:
            max_mb = self.MAX_FILE_SIZE / (1024 * 1024)
            return False, f"Arquivo muito grande. Máximo: {max_mb:.0f}MB"

        if size == 0:
            return False, "Arquivo vazio"

        # Verificar MIME type real (lendo magic bytes)
        mime_type = self._detect_mime_type(file)
        if mime_type not in self.ALLOWED_MIME_TYPES:
            return False, f"Tipo de arquivo não permitido: {mime_type}"

        # Verificar extensão
        ext = Path(file.filename).suffix.lower()
        allowed_exts = self.ALLOWED_MIME_TYPES.get(mime_type, [])
        if ext not in allowed_exts:
            return False, f"Extensão não corresponde ao tipo de arquivo"

        return True, None

    def _detect_mime_type(self, file: FileStorage) -> str:
        """
        Detecta MIME type real do arquivo lendo os magic bytes.
        Mais seguro que confiar na extensão.
        NUNCA confia apenas na extensão do arquivo.
        """
        file.seek(0)
        header = file.read(16)
        file.seek(0)

        # Magic bytes para tipos comuns
        if header[:3] == b'\xff\xd8\xff':
            return 'image/jpeg'
        elif header[:8] == b'\x89PNG\r\n\x1a\n':
            return 'image/png'
        elif header[:6] in (b'GIF87a', b'GIF89a'):
            return 'image/gif'
        elif header[:4] == b'RIFF' and len(header) >= 12 and header[8:12] == b'WEBP':
            return 'image/webp'

        # Se não detectou pelos magic bytes, é tipo desconhecido
        # NÃO usa fallback para evitar aceitar arquivos maliciosos
        return 'application/octet-stream'

    # ==================== PROCESSAMENTO ====================

    def process(self, file: FileStorage, convert_to_webp: bool = True) -> ProcessedImage:
        """
        Processa arquivo de imagem completo.

        1. Valida o arquivo
        2. Gera nome único
        3. Remove metadados EXIF
        4. Cria variantes (thumb, medium, large)
        5. Opcionalmente converte para WebP

        Args:
            file: Arquivo enviado
            convert_to_webp: Se True, converte para WebP (recomendado)

        Returns:
            ProcessedImage com todas as variantes

        Raises:
            MediaValidationError se validação falhar
        """
        # Validar
        is_valid, error = self.validate_file(file)
        if not is_valid:
            raise MediaValidationError(error)

        # Gerar nome único
        original_name = secure_filename(file.filename)
        unique_id = uuid.uuid4().hex[:12]
        timestamp = datetime.now().strftime('%Y%m%d')
        base_name = f"{timestamp}_{unique_id}"

        # Determinar extensão de saída
        output_ext = ".webp" if convert_to_webp else Path(original_name).suffix.lower()

        # Abrir imagem com Pillow
        file.seek(0)
        try:
            img = Image.open(file)
        except Exception as e:
            raise MediaValidationError(f"Arquivo de imagem inválido: {str(e)}")

        # Corrigir orientação baseado em EXIF
        img = self._fix_orientation(img)

        # Converter para RGB se necessário (para WebP/JPEG)
        if img.mode in ('RGBA', 'P') and output_ext in ('.jpg', '.jpeg'):
            img = img.convert('RGB')
        elif img.mode == 'P':
            img = img.convert('RGBA')

        # Processar variantes
        variants = {}

        # Salvar original
        original_filename = f"{base_name}_original{Path(original_name).suffix.lower()}"
        original_path = self.upload_folder / "original" / original_filename
        file.seek(0)
        file.save(str(original_path))

        variants["original"] = ImageVariant(
            size=ImageSize.ORIGINAL,
            path=str(original_path),
            url=f"{self.url_prefix}/original/{original_filename}",
            width=img.width,
            height=img.height,
            file_size=original_path.stat().st_size
        )

        # Criar variantes redimensionadas
        for size, config in self.SIZE_CONFIG.items():
            variant_filename = f"{base_name}_{size.value}{output_ext}"
            variant_path = self.upload_folder / size.value / variant_filename

            # Redimensionar
            resized = self._resize_image(
                img.copy(),
                config["max_width"],
                config["max_height"]
            )

            # Salvar
            save_kwargs = {"quality": config["quality"], "optimize": True}
            if output_ext == ".webp":
                save_kwargs["method"] = 6  # Melhor compressão

            resized.save(str(variant_path), **save_kwargs)

            variants[size.value] = ImageVariant(
                size=size,
                path=str(variant_path),
                url=f"{self.url_prefix}/{size.value}/{variant_filename}",
                width=resized.width,
                height=resized.height,
                file_size=variant_path.stat().st_size
            )

            log_request(
                f"Variante criada: {size.value}",
                level="debug",
                width=resized.width,
                height=resized.height,
                file_size=variant_path.stat().st_size
            )

        # Fechar imagem original
        img.close()

        result = ProcessedImage(
            original_name=original_name,
            stored_name=base_name,
            content_type=self._detect_mime_type(file),
            variants=variants,
            primary_url=variants["medium"].url,
            thumb_url=variants["thumb"].url,
            created_at=datetime.now()
        )

        log_request(
            "Imagem processada com sucesso",
            original=original_name,
            variants=len(variants)
        )

        return result

    def _resize_image(self, img: Image.Image, max_width: int, max_height: int) -> Image.Image:
        """
        Redimensiona imagem mantendo proporção.
        Usa LANCZOS para melhor qualidade.
        """
        # Calcular novo tamanho mantendo proporção
        ratio = min(max_width / img.width, max_height / img.height)

        # Só redimensiona se a imagem for maior
        if ratio < 1:
            new_width = int(img.width * ratio)
            new_height = int(img.height * ratio)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        return img

    def _fix_orientation(self, img: Image.Image) -> Image.Image:
        """
        Corrige orientação da imagem baseado em dados EXIF.
        Câmeras de celular frequentemente salvam imagens rotacionadas.
        """
        try:
            # Usar ImageOps.exif_transpose que faz isso automaticamente
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass  # Se falhar, ignora silenciosamente

        return img

    # ==================== UTILITÁRIOS ====================

    def delete_image(self, stored_name: str) -> int:
        """
        Deleta todas as variantes de uma imagem.

        Args:
            stored_name: Nome base da imagem (sem extensão)

        Returns:
            Número de arquivos deletados
        """
        deleted = 0

        for size in ImageSize:
            folder = self.upload_folder / size.value
            for file in folder.glob(f"{stored_name}*"):
                try:
                    file.unlink()
                    deleted += 1
                except Exception as e:
                    log_error(f"Erro ao deletar {file}", exception=e)

        if deleted > 0:
            log_request(f"Imagem deletada", stored_name=stored_name, files_deleted=deleted)

        return deleted

    def get_image_urls(self, stored_name: str) -> Dict[str, str]:
        """
        Retorna URLs de todas as variantes de uma imagem.

        Args:
            stored_name: Nome base da imagem

        Returns:
            Dict com size -> url
        """
        urls = {}

        for size in ImageSize:
            folder = self.upload_folder / size.value
            for file in folder.glob(f"{stored_name}*"):
                urls[size.value] = f"{self.url_prefix}/{size.value}/{file.name}"
                break

        return urls

    def cleanup_orphans(self, valid_names: List[str]) -> int:
        """
        Remove arquivos órfãos (não referenciados no banco).

        Args:
            valid_names: Lista de stored_names válidos

        Returns:
            Número de arquivos removidos
        """
        removed = 0
        valid_set = set(valid_names)

        for size in ImageSize:
            folder = self.upload_folder / size.value
            for file in folder.iterdir():
                if file.is_file():
                    # Extrair stored_name do arquivo
                    name_parts = file.stem.split('_')
                    if len(name_parts) >= 2:
                        stored_name = f"{name_parts[0]}_{name_parts[1]}"
                        if stored_name not in valid_set:
                            try:
                                file.unlink()
                                removed += 1
                            except Exception as e:
                                log_error(f"Erro ao remover órfão {file}", exception=e)

        if removed > 0:
            log_request(f"Limpeza de órfãos concluída", files_removed=removed)

        return removed

    def get_stats(self) -> Dict:
        """Retorna estatísticas de uso de armazenamento"""
        stats = {
            "total_files": 0,
            "total_size": 0,
            "by_size": {}
        }

        for size in ImageSize:
            folder = self.upload_folder / size.value
            files = list(folder.glob("*"))
            folder_size = sum(f.stat().st_size for f in files if f.is_file())

            stats["by_size"][size.value] = {
                "files": len(files),
                "size_bytes": folder_size,
                "size_mb": round(folder_size / (1024 * 1024), 2)
            }
            stats["total_files"] += len(files)
            stats["total_size"] += folder_size

        stats["total_size_mb"] = round(stats["total_size"] / (1024 * 1024), 2)
        return stats


# ==================== INSTÂNCIA GLOBAL ====================

_pipeline: Optional[MediaPipeline] = None


def get_media_pipeline() -> MediaPipeline:
    """Obtém instância global do pipeline"""
    global _pipeline
    if _pipeline is None:
        from config import Config
        _pipeline = MediaPipeline(
            upload_folder=Config.UPLOAD_FOLDER,
            url_prefix="/static/uploads"
        )
    return _pipeline


def process_upload(file: FileStorage, convert_to_webp: bool = True) -> ProcessedImage:
    """
    Helper para processar upload de forma simples.

    Uso:
        result = process_upload(request.files['image'])
        db.save(image_url=result.primary_url)
    """
    pipeline = get_media_pipeline()
    return pipeline.process(file, convert_to_webp)
