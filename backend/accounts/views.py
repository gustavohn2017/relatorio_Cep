"""
accounts/views.py — Views de autenticação (tradicional + social).

Endpoints:
  POST /api/auth/register/                → Registra novo usuário
  POST /api/auth/token/                   → Obtém par access/refresh (login)
  POST /api/auth/token/refresh/           → Renova access token
  GET  /api/auth/me/                      → Dados do usuário logado
  POST /api/auth/password-reset/          → Envia e-mail de recuperação
  POST /api/auth/password-reset-confirm/  → Confirma nova senha
  POST /api/auth/social/google/           → Login/cadastro via Google
"""

import logging
from datetime import timedelta

import requests as http_requests
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import send_mail
from django.conf import settings

from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_auth_requests

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Profile, SocialAccount
from .serializers import RegisterSerializer, ProfileSerializer

logger = logging.getLogger(__name__)


# -------------------------------------------------------
# Helpers
# -------------------------------------------------------
def _find_or_create_user(email, name, provider, provider_uid, access_token="", refresh_token="", expires_in=3600):
    """Encontra ou cria um usuário a partir de dados OAuth.

    1. Busca SocialAccount existente pelo provider + uid.
    2. Caso contrário, busca User pelo e-mail e vincula.
    3. Caso contrário, cria User + Profile + SocialAccount.
    Retorna o User.
    """
    # 1) SocialAccount existente
    try:
        social = SocialAccount.objects.get(provider=provider, provider_uid=provider_uid)
        user = social.user
        social.access_token = access_token
        if refresh_token:
            social.refresh_token = refresh_token
        social.token_expires_at = timezone.now() + timedelta(seconds=expires_in)
        social.save(update_fields=["access_token", "refresh_token", "token_expires_at"])
        return user
    except SocialAccount.DoesNotExist:
        pass

    # 2) Usuário existente com mesmo e-mail
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        # 3) Criar novo usuário
        base = email.split("@")[0]
        username = base
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base}{counter}"
            counter += 1

        user = User.objects.create_user(username=username, email=email, password=None)
        parts = name.split() if name else []
        user.first_name = parts[0] if parts else ""
        user.last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
        user.save(update_fields=["first_name", "last_name"])
        Profile.objects.get_or_create(user=user)

    # Vincula conta social
    SocialAccount.objects.create(
        user=user,
        provider=provider,
        provider_uid=provider_uid,
        email=email,
        access_token=access_token,
        refresh_token=refresh_token,
        token_expires_at=timezone.now() + timedelta(seconds=expires_in),
    )
    return user


def _jwt_for_user(user):
    """Gera par access/refresh JWT para o usuário."""
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


# -------------------------------------------------------
# Login Social — Google
# -------------------------------------------------------
class GoogleLoginView(APIView):
    """Recebe authorization code do Google, troca por tokens,
    cria ou vincula usuário e retorna JWT."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        code = request.data.get("code")
        redirect_uri = request.data.get("redirect_uri", "")

        if not code:
            return Response(
                {"detail": "Código de autorização é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Trocar code por tokens
        try:
            token_resp = http_requests.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
                    "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
                timeout=15,
            )
        except http_requests.RequestException:
            return Response(
                {"detail": "Erro de comunicação com o Google."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        if token_resp.status_code != 200:
            logger.error("Google token exchange failed: %s", token_resp.text)
            return Response(
                {"detail": "Falha ao trocar código de autorização do Google."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token_data = token_resp.json()
        g_access = token_data.get("access_token", "")
        g_refresh = token_data.get("refresh_token", "")
        g_id_token = token_data.get("id_token", "")
        expires_in = token_data.get("expires_in", 3600)

        # Verificar id_token
        try:
            idinfo = google_id_token.verify_oauth2_token(
                g_id_token,
                google_auth_requests.Request(),
                settings.GOOGLE_OAUTH_CLIENT_ID,
            )
        except ValueError:
            return Response(
                {"detail": "Token do Google inválido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = idinfo.get("email")
        name = idinfo.get("name", "")
        google_uid = idinfo.get("sub")

        if not email:
            return Response(
                {"detail": "E-mail não disponível na conta Google."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = _find_or_create_user(
            email=email,
            name=name,
            provider="google",
            provider_uid=google_uid,
            access_token=g_access,
            refresh_token=g_refresh,
            expires_in=expires_in,
        )

        return Response(_jwt_for_user(user), status=status.HTTP_200_OK)


# -------------------------------------------------------
# Registro (tradicional)
# -------------------------------------------------------
class RegisterView(APIView):
    """Cria uma nova conta de usuário."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = serializer.save()
            return Response(
                {"id": user.id, "username": user.username, "email": user.email},
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            logger.exception("Erro ao registrar usuário")
            return Response(
                {"detail": "Erro interno ao criar conta. Tente novamente."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# -------------------------------------------------------
# Dados do usuário autenticado
# -------------------------------------------------------
class MeView(APIView):
    """Retorna perfil do usuário autenticado."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            # Cria perfil automaticamente se não existir
            profile = Profile.objects.create(user=request.user)

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
        frontend_url = getattr(settings, "FRONTEND_URL", "").rstrip("/")
        if not frontend_url:
            frontend_url = f"{request.scheme}://{request.get_host()}"
        reset_link = f"{frontend_url}/reset-password/{uid}/{token}"

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
