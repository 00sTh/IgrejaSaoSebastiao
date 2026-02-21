from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from apps.contact.views import SendMessageView
from apps.dashboard.admin import igreja_admin_site
from apps.parish.views import IndexView

urlpatterns = [
    path("admin/", igreja_admin_site.urls),
    path("api/enviar-mensagem", SendMessageView.as_view(), name="enviar-mensagem"),
    path("", IndexView.as_view(), name="index"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    try:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
    except ImportError:
        pass
