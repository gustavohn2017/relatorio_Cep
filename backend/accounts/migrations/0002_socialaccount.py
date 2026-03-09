# Generated migration for SocialAccount model

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SocialAccount",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "provider",
                    models.CharField(
                        choices=[("google", "Google"), ("microsoft", "Microsoft")],
                        max_length=20,
                    ),
                ),
                ("provider_uid", models.CharField(max_length=255)),
                ("email", models.EmailField(max_length=254)),
                ("access_token", models.TextField(blank=True, default="")),
                ("refresh_token", models.TextField(blank=True, default="")),
                (
                    "token_expires_at",
                    models.DateTimeField(blank=True, null=True),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="social_accounts",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Conta Social",
                "verbose_name_plural": "Contas Sociais",
                "unique_together": {("provider", "provider_uid")},
            },
        ),
    ]
