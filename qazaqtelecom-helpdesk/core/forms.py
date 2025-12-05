from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


class UserRegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = [
            "username",
            "full_name",
            "phone",
            "language",
            "password1",
            "password2",
        ]


class LanguageForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["language"]
