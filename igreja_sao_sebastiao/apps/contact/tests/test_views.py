import json

import pytest

from apps.contact.models import ContactMessage


@pytest.mark.django_db
class TestSendMessageView:
    URL = "/api/enviar-mensagem"

    def test_send_valid_message(self, client):
        data = {
            "nome": "João Silva",
            "email": "joao@example.com",
            "mensagem": "Gostaria de saber sobre os horários das missas.",
        }
        response = client.post(self.URL, json.dumps(data), content_type="application/json")
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "success"
        assert ContactMessage.objects.count() == 1
        msg = ContactMessage.objects.first()
        assert msg.nome == "João Silva"
        assert msg.lida is False

    def test_missing_fields(self, client):
        data = {"nome": "João", "email": ""}
        response = client.post(self.URL, json.dumps(data), content_type="application/json")
        assert response.status_code == 400

    def test_invalid_name_single_word(self, client):
        data = {
            "nome": "João",
            "email": "joao@example.com",
            "mensagem": "Uma mensagem de teste longa o suficiente.",
        }
        response = client.post(self.URL, json.dumps(data), content_type="application/json")
        assert response.status_code == 400
        assert "sobrenome" in response.json()["message"]

    def test_disposable_email_blocked(self, client):
        data = {
            "nome": "João Silva",
            "email": "joao@mailinator.com",
            "mensagem": "Uma mensagem de teste longa o suficiente.",
        }
        response = client.post(self.URL, json.dumps(data), content_type="application/json")
        assert response.status_code == 400
        assert "permanente" in response.json()["message"]

    def test_short_message(self, client):
        data = {
            "nome": "João Silva",
            "email": "joao@example.com",
            "mensagem": "Oi",
        }
        response = client.post(self.URL, json.dumps(data), content_type="application/json")
        assert response.status_code == 400

    def test_invalid_json(self, client):
        response = client.post(self.URL, "not json", content_type="application/json")
        assert response.status_code == 400
