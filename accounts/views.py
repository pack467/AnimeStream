from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import render, redirect
from django.urls import reverse


def auth_page(request):
    if request.user.is_authenticated:
        return redirect("home")
    return render(request, "auth/login.html")


def login_view(request):
    if request.method != "POST":
        return redirect("auth")

    identifier = (request.POST.get("email") or "").strip()   # Email or Username
    password = request.POST.get("password") or ""
    remember = request.POST.get("remember") == "on"

    # Boleh login pakai email atau username
    user_obj = User.objects.filter(
        Q(username__iexact=identifier) | Q(email__iexact=identifier)
    ).first()

    username = user_obj.username if user_obj else identifier
    user = authenticate(request, username=username, password=password)

    if user is None:
        messages.error(request, "Email/Username atau password salah.")
        return redirect("auth")

    login(request, user)

    # Remember me: kalau tidak dicentang, session habis saat browser ditutup
    if not remember:
        request.session.set_expiry(0)

    # flag untuk preloader sekali saja
    return redirect(reverse("home") + "?from=login")


def register_view(request):
    if request.method != "POST":
        return redirect("auth")

    username = (request.POST.get("username") or "").strip()
    email = (request.POST.get("email") or "").strip()
    password = request.POST.get("password") or ""
    confirm = request.POST.get("confirmPassword") or ""
    agree = request.POST.get("agreeTerms") == "on"

    if not agree:
        messages.error(request, "Kamu harus menyetujui Terms & Privacy Policy.")
        return redirect("auth")

    if password != confirm:
        messages.error(request, "Password dan Confirm Password tidak sama.")
        return redirect("auth")

    if User.objects.filter(username__iexact=username).exists():
        messages.error(request, "Username sudah digunakan.")
        return redirect("auth")

    if User.objects.filter(email__iexact=email).exists():
        messages.error(request, "Email sudah terdaftar.")
        return redirect("auth")

    User.objects.create_user(username=username, email=email, password=password)

    user = authenticate(request, username=username, password=password)
    login(request, user)
    return redirect(reverse("home") + "?from=login")


def logout_view(request):
    logout(request)
    return redirect("auth")
