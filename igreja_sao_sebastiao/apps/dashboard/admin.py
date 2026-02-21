"""
Custom admin views: Dashboard, Site Content Editor, Site Images, Image Bank.
Registered as extra admin URLs in the custom AdminSite.
"""

import os

from django.conf import settings
from django.shortcuts import redirect, render
from django.urls import path
from unfold.sites import UnfoldAdminSite

from apps.contact.models import ContactMessage
from apps.gallery.models import GalleryImage
from apps.parish.models import MassSchedule, News, SiteContent


class IgrejaAdminSite(UnfoldAdminSite):
    """Custom AdminSite with additional views."""

    site_header = "Igreja São Sebastião"
    site_title = "Administração"
    index_title = "Painel Administrativo"

    def get_urls(self):
        custom_urls = [
            path("dashboard/", self.admin_view(self.dashboard_view), name="dashboard"),
            path("site-content/", self.admin_view(self.site_content_view), name="site-content"),
            path("site-content/save/", self.admin_view(self.site_content_save), name="site-content-save"),
            path("site-images/", self.admin_view(self.site_images_view), name="site-images"),
            path("image-bank/", self.admin_view(self.image_bank_view), name="image-bank"),
        ]
        return custom_urls + super().get_urls()

    def index(self, request, extra_context=None):
        return redirect("admin:dashboard")

    def dashboard_view(self, request):
        context = {
            **self.each_context(request),
            "title": "Dashboard",
            "stats": {
                "noticias": News.objects.count(),
                "noticias_publicadas": News.objects.filter(publicado=True).count(),
                "horarios": MassSchedule.objects.filter(ativo=True).count(),
                "fotos": GalleryImage.objects.filter(ativo=True).count(),
                "mensagens_nao_lidas": ContactMessage.objects.filter(lida=False).count(),
                "mensagens_total": ContactMessage.objects.count(),
            },
            "noticias_recentes": News.objects.order_by("-data_criacao")[:5],
            "mensagens_recentes": ContactMessage.objects.filter(lida=False)[:5],
        }
        return render(request, "admin/dashboard.html", context)

    def site_content_view(self, request):
        sections = SiteContent.objects.all()

        groups = {
            "Banner (Hero)": [],
            "Sobre a Paróquia": [],
            "Horários": [],
            "Galeria": [],
            "História": [],
            "Localização": [],
            "Contato": [],
            "Rodapé e Redes": [],
        }

        prefix_map = {
            "hero_": "Banner (Hero)",
            "sobre_": "Sobre a Paróquia",
            "horarios_": "Horários",
            "missas_": "Horários",
            "confissoes_": "Horários",
            "secretaria_": "Horários",
            "galeria_": "Galeria",
            "historia_": "História",
            "localizacao_": "Localização",
            "contato_": "Contato",
            "rodape_": "Rodapé e Redes",
            "redes_": "Rodapé e Redes",
        }

        for section in sections:
            placed = False
            for prefix, group_name in prefix_map.items():
                if section.secao.startswith(prefix):
                    groups[group_name].append(section)
                    placed = True
                    break
            if not placed:
                groups.setdefault("Outros", []).append(section)

        groups = {k: v for k, v in groups.items() if v}

        context = {
            **self.each_context(request),
            "title": "Conteúdo do Site",
            "groups": groups,
        }
        return render(request, "admin/site_content_editor.html", context)

    def site_content_save(self, request):
        if request.method != "POST":
            return redirect("admin:site-content")

        for key, value in request.POST.items():
            if key.startswith("titulo_"):
                secao = key[7:]
                conteudo = request.POST.get(f"conteudo_{secao}", "")
                try:
                    sc = SiteContent.objects.get(secao=secao)
                    sc.titulo = value
                    sc.conteudo = conteudo
                    sc.save()
                except SiteContent.DoesNotExist:
                    pass

        return redirect("admin:site-content")

    def site_images_view(self, request):
        if request.method == "POST" and request.FILES:
            for field_name, uploaded_file in request.FILES.items():
                dest_map = {
                    "hero_image": "img/hero-background.jpg",
                    "about_image": "img/Comunidade_acolhedora.jpg",
                    "logo_image": "img/logo.png",
                }
                dest_path = dest_map.get(field_name)
                if dest_path:
                    full_path = os.path.join(settings.STATICFILES_DIRS[0], dest_path)
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    with open(full_path, "wb") as f:
                        for chunk in uploaded_file.chunks():
                            f.write(chunk)

            return redirect("admin:site-images")

        images = {}
        for name, path_str in [
            ("hero", "img/hero-background.jpg"),
            ("about", "img/Comunidade_acolhedora.jpg"),
            ("logo", "img/logo.png"),
        ]:
            full_path = os.path.join(settings.STATICFILES_DIRS[0], path_str)
            images[name] = {
                "exists": os.path.exists(full_path),
                "url": f"{settings.STATIC_URL}{path_str}",
            }

        context = {
            **self.each_context(request),
            "title": "Imagens do Site",
            "images": images,
        }
        return render(request, "admin/site_images.html", context)

    def image_bank_view(self, request):
        images = []
        media_root = settings.MEDIA_ROOT
        if os.path.exists(media_root):
            for root, _dirs, files in os.walk(media_root):
                for f in files:
                    if f.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")):
                        full_path = os.path.join(root, f)
                        rel_path = os.path.relpath(full_path, media_root)
                        images.append(
                            {
                                "name": f,
                                "url": f"{settings.MEDIA_URL}{rel_path}",
                                "size": os.path.getsize(full_path),
                            }
                        )

        images.sort(key=lambda x: x["name"])

        context = {
            **self.each_context(request),
            "title": "Banco de Imagens",
            "images": images,
        }
        return render(request, "admin/image_bank.html", context)


# Replace default admin site
igreja_admin_site = IgrejaAdminSite(name="admin")


def _register_models():
    """Register all models with the custom admin site."""
    from django.contrib.auth.models import Group

    from apps.accounts.admin import AuditLogAdmin, UserAdmin
    from apps.accounts.models import AuditLog, User
    from apps.contact.admin import ContactMessageAdmin
    from apps.contact.models import ContactMessage as ContactMessageModel
    from apps.gallery.admin import GalleryImageAdmin
    from apps.gallery.models import GalleryImage as GalleryImageModel
    from apps.parish.admin import (
        ContactInfoAdmin,
        MassScheduleAdmin,
        NewsAdmin,
        SiteConfigurationAdmin,
        SiteContentAdmin,
    )
    from apps.parish.models import ContactInfo, SiteConfiguration
    from apps.parish.models import MassSchedule as MassScheduleModel
    from apps.parish.models import News as NewsModel
    from apps.parish.models import SiteContent as SiteContentModel

    igreja_admin_site.register(User, UserAdmin)
    igreja_admin_site.register(AuditLog, AuditLogAdmin)
    igreja_admin_site.register(Group)
    igreja_admin_site.register(NewsModel, NewsAdmin)
    igreja_admin_site.register(MassScheduleModel, MassScheduleAdmin)
    igreja_admin_site.register(SiteContentModel, SiteContentAdmin)
    igreja_admin_site.register(SiteConfiguration, SiteConfigurationAdmin)
    igreja_admin_site.register(ContactInfo, ContactInfoAdmin)
    igreja_admin_site.register(GalleryImageModel, GalleryImageAdmin)
    igreja_admin_site.register(ContactMessageModel, ContactMessageAdmin)


_register_models()
