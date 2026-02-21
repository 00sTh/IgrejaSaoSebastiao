import json

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .models import ContactMessage
from .validators import validate_email_not_disposable, validate_name_brazilian


@method_decorator(csrf_exempt, name="dispatch")
class SendMessageView(View):
    """API endpoint for the public contact form."""

    def post(self, request):
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({"status": "error", "message": "Dados inválidos."}, status=400)

        nome = data.get("nome", "").strip()
        email = data.get("email", "").strip()
        mensagem = data.get("mensagem", "").strip()

        # Validate required fields
        if not all([nome, email, mensagem]):
            return JsonResponse({"status": "error", "message": "Todos os campos são obrigatórios."}, status=400)

        # Validate name
        try:
            validate_name_brazilian(nome)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e.message)}, status=400)

        # Validate email domain
        try:
            validate_email_not_disposable(email)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e.message)}, status=400)

        # Validate message length
        if len(mensagem) < 10:
            return JsonResponse(
                {"status": "error", "message": "A mensagem deve ter pelo menos 10 caracteres."}, status=400
            )

        ContactMessage.objects.create(nome=nome, email=email, mensagem=mensagem)

        return JsonResponse(
            {
                "status": "success",
                "message": "Mensagem enviada com sucesso! Entraremos em contato em breve.",
            }
        )
