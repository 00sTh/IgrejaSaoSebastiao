"""
Creates default permission groups: Administrador, Editor, Visualizador.
Run: python manage.py setup_groups
"""

from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Creates default permission groups for the parish admin"

    def handle(self, *args, **options):
        # Administrador - full access
        admin_group, created = Group.objects.get_or_create(name="Administrador")
        if created:
            admin_group.permissions.set(Permission.objects.all())
            self.stdout.write(self.style.SUCCESS("  Grupo 'Administrador' criado com todas as permissões"))
        else:
            self.stdout.write("  Grupo 'Administrador' já existe")

        # Editor - can add/change content but not delete users or config
        editor_group, created = Group.objects.get_or_create(name="Editor")
        if created:
            editor_perms = (
                Permission.objects.filter(
                    content_type__app_label__in=["parish", "gallery", "contact"],
                    codename__startswith="change",
                )
                | Permission.objects.filter(
                    content_type__app_label__in=["parish", "gallery"],
                    codename__startswith="add",
                )
                | Permission.objects.filter(
                    content_type__app_label="contact",
                    codename="view_contactmessage",
                )
                | Permission.objects.filter(
                    content_type__app_label__in=["parish", "gallery", "contact"],
                    codename__startswith="view",
                )
            )
            editor_group.permissions.set(editor_perms.distinct())
            self.stdout.write(self.style.SUCCESS("  Grupo 'Editor' criado"))
        else:
            self.stdout.write("  Grupo 'Editor' já existe")

        # Visualizador - read-only
        viewer_group, created = Group.objects.get_or_create(name="Visualizador")
        if created:
            viewer_perms = Permission.objects.filter(codename__startswith="view")
            viewer_group.permissions.set(viewer_perms)
            self.stdout.write(self.style.SUCCESS("  Grupo 'Visualizador' criado"))
        else:
            self.stdout.write("  Grupo 'Visualizador' já existe")

        self.stdout.write(self.style.SUCCESS("Grupos configurados com sucesso!"))
