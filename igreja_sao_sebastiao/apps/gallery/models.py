from django.db import models


class GalleryImage(models.Model):
    """Photo gallery image with auto-generated variants."""

    class Category(models.TextChoices):
        IGREJA = "igreja", "Igreja"
        EVENTOS = "eventos", "Eventos"
        COMUNIDADE = "comunidade", "Comunidade"
        FESTAS = "festas", "Festas"
        OUTROS = "outros", "Outros"

    titulo = models.CharField("título", max_length=200)
    descricao = models.TextField("descrição", blank=True)
    categoria = models.CharField("categoria", max_length=15, choices=Category.choices, default=Category.OUTROS)
    imagem = models.ImageField("imagem original", upload_to="galeria/%Y/%m/")
    imagem_thumb = models.ImageField("miniatura", upload_to="galeria/thumbs/", blank=True)
    imagem_medium = models.ImageField("média", upload_to="galeria/medium/", blank=True)
    imagem_large = models.ImageField("grande", upload_to="galeria/large/", blank=True)
    ativo = models.BooleanField("ativo", default=True)
    data_upload = models.DateTimeField("data de upload", auto_now_add=True)

    class Meta:
        verbose_name = "imagem da galeria"
        verbose_name_plural = "imagens da galeria"
        ordering = ["-data_upload"]

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new and self.imagem:
            from .services import process_gallery_image

            process_gallery_image(self)
