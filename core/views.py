from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import LanguageForm, UserRegisterForm


def index(request):
    return render(request, "core/index.html")


@login_required
def chat(request):
    return render(request, "core/chat.html")


def register(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = user.ROLE_CLIENT
            user.save()
            login(request, user)
            return redirect("core:chat")
    else:
        form = UserRegisterForm()
    return render(request, "core/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("core:chat")
        messages.error(request, "Неверный логин или пароль")
    return render(request, "core/login.html")


def logout_view(request):
    logout(request)
    return redirect("core:login")


@login_required
@require_POST
def set_language(request):
    form = LanguageForm(request.POST, instance=request.user)
    if form.is_valid():
        form.save()
    next_url = request.META.get("HTTP_REFERER") or "core:index"
    return redirect(next_url)
