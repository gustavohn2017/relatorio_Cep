from django.contrib import admin
from .models import Profile, SocialAccount

admin.site.register(Profile)


@admin.register(SocialAccount)
class SocialAccountAdmin(admin.ModelAdmin):
    list_display = ("user", "provider", "email", "token_expires_at")
    list_filter = ("provider",)
    search_fields = ("email", "user__username")
