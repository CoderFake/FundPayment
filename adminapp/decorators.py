from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from functools import wraps
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


def user_is_active(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(reverse('adminapp:admin_login'))
        if not request.user.is_active:
            messages.error(request, "Tài khoản của bạn chưa được kích hoạt")
            return redirect(reverse('adminapp:admin_login'))
        return view_func(request, *args, **kwargs)

    return wrapper


def user_is_staff(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_staff:
            messages.error(request, "Bạn không có quyền truy cập trang này")
            return redirect(reverse('adminapp:admin_login'))
        return view_func(request, *args, **kwargs)

    return wrapper


def user_is_superuser(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_superuser:
            messages.error(request, "Bạn không có quyền admin")
            return redirect(reverse('adminapp:admin_login'))
        return view_func(request, *args, **kwargs)

    return wrapper


def user_passes_test(is_active=False, is_staff=False, is_superuser=False):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')

            if is_active and not request.user.is_active:
                return HttpResponseForbidden("Tài khoản chưa được kích hoạt")

            if is_staff and not request.user.is_staff:
                return HttpResponseForbidden("Bạn không có quyền staff")

            if is_superuser and not request.user.is_superuser:
                return HttpResponseForbidden("Bạn không có quyền admin")

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator