"""
accounts/serializers.py — Serializadores para registro, login e perfil.
"""

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Profile


class RegisterSerializer(serializers.ModelSerializer):
    """Registro de novo usuário com validação de senha."""

    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "email", "password", "password_confirm")

    # Garante que as duas senhas coincidam
    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "As senhas não coincidem."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )
        # Cria perfil automaticamente
        Profile.objects.create(user=user)
        return user


class UserSerializer(serializers.ModelSerializer):
    """Dados públicos do usuário."""

    class Meta:
        model = User
        fields = ("id", "username", "email")
        read_only_fields = fields


class ProfileSerializer(serializers.ModelSerializer):
    """Dados do perfil, incluindo informações do usuário."""

    user = UserSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = ("id", "user", "avatar", "created_at")
        read_only_fields = ("id", "created_at")
