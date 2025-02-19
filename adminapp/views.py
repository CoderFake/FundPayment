from admin_soft.forms import RegistrationForm
from django.contrib import messages
from django.urls import reverse

from .forms import LoginForm
from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect


class UserLoginView(LoginView):
   template_name = 'accounts/login.html'
   form_class = LoginForm

   def form_invalid(self, form):
       messages.error(
           self.request,
           "Tên đăng nhập hoặc mật khẩu không chính xác"
       )
       return super().form_invalid(form)


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            print('Account created successfully!')
            return redirect(reverse('login'))
        else:
            print("Register failed!")
    else:
        form = RegistrationForm()

    context = {'form': form}
    return render(request, 'accounts/register.html', context)


def logout_view(request):
    logout(request)
    return redirect(reverse('login'))
