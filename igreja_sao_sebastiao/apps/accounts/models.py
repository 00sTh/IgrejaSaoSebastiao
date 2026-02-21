from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model for the parish site."""

    email = models.EmailField("e-mail", unique=True)
    failed_login_attempts = models.PositiveIntegerField("tentativas de login falhas", default=0)
    last_failed_login = models.DateTimeField("último login falho", null=True, blank=True)

    class Meta:
        verbose_name = "usuário"
        verbose_name_plural = "usuários"
        ordering = ["-date_joined"]

    def __str__(self):
        return self.get_full_name() or self.username


class AuditLog(models.Model):
    """Tracks admin actions for accountability."""

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="usuário",
        related_name="audit_logs",
    )
    action = models.CharField("ação", max_length=100)
    entity_type = models.CharField("tipo de entidade", max_length=100, blank=True)
    entity_id = models.CharField("ID da entidade", max_length=50, blank=True)
    old_value = models.JSONField("valor anterior", null=True, blank=True)
    new_value = models.JSONField("valor novo", null=True, blank=True)
    ip_address = models.GenericIPAddressField("endereço IP", null=True, blank=True)
    created_at = models.DateTimeField("data", auto_now_add=True)

    class Meta:
        verbose_name = "log de auditoria"
        verbose_name_plural = "logs de auditoria"
        ordering = ["-created_at"]

    def __str__(self):
        user_str = self.user.username if self.user else "sistema"
        return f"{user_str} - {self.action} ({self.created_at:%d/%m/%Y %H:%M})"
