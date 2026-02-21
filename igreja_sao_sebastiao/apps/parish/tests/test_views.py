import pytest

from apps.parish.models import MassSchedule, News


@pytest.mark.django_db
class TestIndexView:
    def test_index_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_index_with_seeded_content(self, client, seeded_content):
        response = client.get("/")
        assert response.status_code == 200
        assert "Igreja São Sebastião" in response.content.decode()

    def test_index_contains_news(self, client):
        News.objects.create(titulo="Notícia Teste", conteudo="Conteúdo")
        response = client.get("/")
        assert "Notícia Teste" in response.content.decode()

    def test_index_contains_schedules(self, client):
        MassSchedule.objects.create(dia_semana="domingo", horario="08:00", tipo="missa")
        response = client.get("/")
        assert "Domingo" in response.content.decode()

    def test_index_context(self, client, seeded_content):
        response = client.get("/")
        ctx = response.context
        assert "noticias" in ctx
        assert "horarios" in ctx
        assert "info_paroquia" in ctx
        assert "galeria" in ctx
        assert "contatos" in ctx
        assert "configs" in ctx
