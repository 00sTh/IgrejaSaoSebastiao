from django.db import models


class News(models.Model):
    """News, events, and announcements."""

    class NewsType(models.TextChoices):
        NOTICIA = "noticia", "Notícia"
        EVENTO = "evento", "Evento"
        AVISO = "aviso", "Aviso"

    titulo = models.CharField("título", max_length=200)
    subtitulo = models.CharField("subtítulo", max_length=300, blank=True)
    conteudo = models.TextField("conteúdo")
    imagem = models.ImageField("imagem", upload_to="noticias/%Y/%m/", blank=True)
    tipo = models.CharField("tipo", max_length=10, choices=NewsType.choices, default=NewsType.NOTICIA)
    publicado = models.BooleanField("publicado", default=True)
    data_criacao = models.DateTimeField("data de criação", auto_now_add=True)
    data_atualizacao = models.DateTimeField("data de atualização", auto_now=True)

    class Meta:
        verbose_name = "notícia"
        verbose_name_plural = "notícias"
        ordering = ["-data_criacao"]

    def __str__(self):
        return self.titulo


class MassSchedule(models.Model):
    """Weekly mass and event schedules."""

    class DayOfWeek(models.TextChoices):
        SEGUNDA = "segunda", "Segunda-feira"
        TERCA = "terca", "Terça-feira"
        QUARTA = "quarta", "Quarta-feira"
        QUINTA = "quinta", "Quinta-feira"
        SEXTA = "sexta", "Sexta-feira"
        SABADO = "sabado", "Sábado"
        DOMINGO = "domingo", "Domingo"

    class ScheduleType(models.TextChoices):
        MISSA = "missa", "Missa"
        MISSA_SOLENE = "missa_solene", "Missa Solene"
        ADORACAO = "adoracao", "Adoração"
        TERCO = "terco", "Terço"

    dia_semana = models.CharField("dia da semana", max_length=10, choices=DayOfWeek.choices)
    horario = models.TimeField("horário")
    tipo = models.CharField("tipo", max_length=15, choices=ScheduleType.choices, default=ScheduleType.MISSA)
    nome = models.CharField("nome/observação", max_length=200, blank=True)
    ativo = models.BooleanField("ativo", default=True)
    ordem = models.PositiveIntegerField("ordem", default=0)

    class Meta:
        verbose_name = "horário de missa"
        verbose_name_plural = "horários de missas"
        ordering = ["ordem", "dia_semana", "horario"]

    def __str__(self):
        return f"{self.get_dia_semana_display()} - {self.horario:%H:%M} ({self.get_tipo_display()})"


class SiteContent(models.Model):
    """CMS key-value content for site sections."""

    secao = models.CharField("seção", max_length=100, unique=True)
    titulo = models.CharField("título/valor", max_length=500)
    conteudo = models.TextField("conteúdo", blank=True)
    ordem = models.PositiveIntegerField("ordem", default=0)

    class Meta:
        verbose_name = "conteúdo do site"
        verbose_name_plural = "conteúdos do site"
        ordering = ["ordem"]

    def __str__(self):
        return f"{self.secao}: {self.titulo[:50]}"


class SiteConfiguration(models.Model):
    """General site configuration key-value pairs."""

    chave = models.CharField("chave", max_length=100, primary_key=True)
    valor = models.TextField("valor")
    descricao = models.CharField("descrição", max_length=300, blank=True)

    class Meta:
        verbose_name = "configuração"
        verbose_name_plural = "configurações"
        ordering = ["chave"]

    def __str__(self):
        return f"{self.chave}: {self.valor[:50]}"


class ContactInfo(models.Model):
    """Parish contact information entries."""

    class ContactType(models.TextChoices):
        TELEFONE = "telefone", "Telefone"
        EMAIL = "email", "E-mail"
        ENDERECO = "endereco", "Endereço"
        WHATSAPP = "whatsapp", "WhatsApp"
        INSTAGRAM = "instagram", "Instagram"
        FACEBOOK = "facebook", "Facebook"

    tipo = models.CharField("tipo", max_length=15, choices=ContactType.choices)
    valor = models.CharField("valor", max_length=300)
    icone = models.CharField("ícone (FontAwesome)", max_length=50, blank=True)
    ordem = models.PositiveIntegerField("ordem", default=0)

    class Meta:
        verbose_name = "informação de contato"
        verbose_name_plural = "informações de contato"
        ordering = ["ordem"]

    def __str__(self):
        return f"{self.get_tipo_display()}: {self.valor}"
