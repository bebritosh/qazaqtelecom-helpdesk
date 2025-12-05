from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CLIENT = "client"
    ROLE_OPERATOR = "operator"
    ROLE_ADMIN = "admin"

    ROLE_CHOICES = [
        (ROLE_CLIENT, "Client"),
        (ROLE_OPERATOR, "Operator"),
        (ROLE_ADMIN, "Admin"),
    ]

    LANGUAGE_RU = "ru"
    LANGUAGE_KK = "kk"

    LANGUAGE_CHOICES = [
        (LANGUAGE_RU, "Русский"),
        (LANGUAGE_KK, "Қазақша"),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_CLIENT)
    full_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default=LANGUAGE_RU)

    def __str__(self) -> str:
        return self.full_name or self.username
