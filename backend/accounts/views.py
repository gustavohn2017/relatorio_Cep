"""
accounts/views.py — Views de autenticação.

Endpoints:
  POST /api/auth/register/         → Registra novo usuário
  POST /api/auth/token/            → Obtém par access/refresh (login)
  POST /api/auth/token/refresh/    → Renova access token
  GET  /api/auth/me/               → Dados do usuário logado
  POST /api/auth/password-reset/   → Envia e-mail de recuperação
  POST /api/auth/password-reset-confirm/ → Confirma nova senha
"""

from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import send_mail
from django.conf import settings

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import RegisterSerializer, ProfileSerializer


# -------------------------------------------------------
# Registro
# -------------------------------------------------------
class RegisterView(generics.CreateAPIView):
    """Cria uma nova conta de usuário."""

    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


# -------------------------------------------------------
# Dados do usuário autenticado
# -------------------------------------------------------
class MeView(APIView):
    """Retorna perfil do usuário autenticado."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = request.user.profile
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)


# -------------------------------------------------------
# Recuperação de senha — solicitar link
# -------------------------------------------------------
class PasswordResetRequestView(APIView):
    """Envia um e-mail com token para redefinição de senha."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email", "").strip()
        if not email:
            return Response(
                {"detail": "Informe o e-mail."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Busca o usuário; se não existir, retorna 200 mesmo assim (segurança)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "Se o e-mail estiver cadastrado, um link será enviado."})

        # Gera token e uid seguros
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Monta link para o frontend
        reset_link = f"{request.scheme}://{request.get_host()}/reset-password/{uid}/{token}"

        send_mail(
            subject="Recuperação de senha — RelatórioCEP",
            message=f"Olá {user.username},\n\nClique no link para redefinir sua senha:\n{reset_link}\n\nSe não solicitou, ignore este e-mail.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        return Response({"detail": "Se o e-mail estiver cadastrado, um link será enviado."})


# -------------------------------------------------------
# Recuperação de senha — confirmar nova senha
# -------------------------------------------------------
class PasswordResetConfirmView(APIView):
    """Recebe uid, token e nova senha para redefinir."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        uid = request.data.get("uid", "")
        token = request.data.get("token", "")
        new_password = request.data.get("new_password", "")

        if not all([uid, token, new_password]):
            return Response(
                {"detail": "uid, token e new_password são obrigatórios."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (User.DoesNotExist, ValueError, TypeError):
            return Response({"detail": "Link inválido."}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({"detail": "Token expirado ou inválido."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({"detail": "Senha redefinida com sucesso."})
