from django.views.generic import TemplateView

from apps.gallery.models import GalleryImage

from .models import ContactInfo, MassSchedule, News, SiteConfiguration, SiteContent


class IndexView(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # News (published, latest 6)
        context["noticias"] = News.objects.filter(publicado=True)[:6]

        # Mass schedules (active)
        context["horarios"] = MassSchedule.objects.filter(ativo=True)

        # Site content as dict by section key
        info_paroquia = {}
        for sc in SiteContent.objects.all():
            info_paroquia[sc.secao] = {"titulo": sc.titulo, "conteudo": sc.conteudo}
        context["info_paroquia"] = info_paroquia

        # Gallery (active, latest 12)
        context["galeria"] = GalleryImage.objects.filter(ativo=True)[:12]

        # Contacts
        context["contatos"] = ContactInfo.objects.all()

        # Configurations as dict
        context["configs"] = {sc.chave: sc.valor for sc in SiteConfiguration.objects.all()}

        return context
