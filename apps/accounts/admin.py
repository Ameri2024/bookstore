from django.contrib import admin
from .models import CustomUser, OTPCode


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ("phone_number", "first_name", "last_name", "email", "is_staff", "is_active")
    search_fields = ("phone_number", "first_name", "last_name", "email")
    list_filter = ("is_staff", "is_active")
    ordering = ("phone_number",)


@admin.register(OTPCode)
class OTPCodeAdmin(admin.ModelAdmin):
    list_display = ("user", "code", "is_used", "created_at", "expires_at")
    search_fields = ("user__phone_number", "code")
    list_filter = ("is_used",)
    ordering = ("-created_at",)