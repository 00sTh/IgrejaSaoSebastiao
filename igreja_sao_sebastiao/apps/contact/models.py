from django.db import models


class ContactMessage(models.Model):
    """Messages submitted through the public contact form."""

    nome = models.CharField("nome", max_length=200)
    email = models.EmailField("e-mail")
    mensagem = models.TextField("mensagem")
    lida = models.BooleanField("lida", default=False)
    data_criacao = models.DateTimeField("data de criação", auto_now_add=True)

    class Meta:
        verbose_name = "mensagem de contato"
        verbose_name_plural = "mensagens de contato"
        ordering = ["-data_criacao"]

    def __str__(self):
        status = "Lida" if self.lida else "Não lida"
        return f"{self.nome} - {status} ({self.data_criacao:%d/%m/%Y})"
