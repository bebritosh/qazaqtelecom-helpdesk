from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Дополнительно", {"fields": ("full_name", "phone", "language", "role")}),
    )
    list_display = ("username", "full_name", "phone", "role", "language", "is_staff")
    list_filter = ("role", "language", "is_staff")
