from datetime import time

import pytest

from apps.parish.models import ContactInfo, MassSchedule, News, SiteConfiguration, SiteContent


@pytest.mark.django_db
class TestNewsModel:
    def test_create_news(self):
        news = News.objects.create(
            titulo="Festa de São Sebastião",
            subtitulo="Celebração anual",
            conteudo="<p>Venha celebrar conosco!</p>",
            tipo="evento",
        )
        assert str(news) == "Festa de São Sebastião"
        assert news.publicado is True
        assert news.data_criacao is not None

    def test_news_ordering(self):
        News.objects.create(titulo="Antiga", conteudo="a")
        News.objects.create(titulo="Nova", conteudo="b")
        noticias = list(News.objects.values_list("titulo", flat=True))
        assert noticias[0] == "Nova"


@pytest.mark.django_db
class TestMassScheduleModel:
    def test_create_schedule(self):
        schedule = MassSchedule.objects.create(
            dia_semana="domingo",
            horario=time(8, 0),
            tipo="missa",
        )
        assert "Domingo" in str(schedule)
        assert "08:00" in str(schedule)

    def test_schedule_with_name(self):
        schedule = MassSchedule.objects.create(
            dia_semana="domingo",
            horario=time(19, 0),
            tipo="missa_solene",
            nome="Missa Solene",
        )
        assert schedule.nome == "Missa Solene"


@pytest.mark.django_db
class TestSiteContentModel:
    def test_create_content(self):
        sc = SiteContent.objects.create(
            secao="hero_titulo",
            titulo="Igreja São Sebastião",
            conteudo="Título principal",
        )
        assert "hero_titulo" in str(sc)

    def test_unique_section(self):
        SiteContent.objects.create(secao="test", titulo="a", conteudo="b")
        from django.db import IntegrityError

        with pytest.raises(IntegrityError):
            SiteContent.objects.create(secao="test", titulo="c", conteudo="d")


@pytest.mark.django_db
class TestSiteConfiguration:
    def test_create_config(self):
        config = SiteConfiguration.objects.create(
            chave="site_nome",
            valor="Igreja São Sebastião",
            descricao="Nome do site",
        )
        assert "site_nome" in str(config)


@pytest.mark.django_db
class TestContactInfo:
    def test_create_contact(self):
        info = ContactInfo.objects.create(
            tipo="telefone",
            valor="(31) 3295-1379",
            icone="fas fa-phone",
        )
        assert "Telefone" in str(info)
