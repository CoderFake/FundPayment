from django import forms
from django.contrib.auth.forms import (
    UserCreationForm,
    AuthenticationForm,
    PasswordChangeForm,
    UsernameField, 
    PasswordResetForm,
    SetPasswordForm
)
from django.utils.translation import gettext_lazy as _


class LoginForm(AuthenticationForm):
   username = UsernameField(
       widget=forms.TextInput(
           attrs={
               "class": "form-control",
               "placeholder": "Username"
           }
       )
   )
   password = forms.CharField(
       label=_("Mật khẩu"),
       strip=False,
       widget=forms.PasswordInput(
           attrs={
               "class": "form-control",
               "placeholder": "Mật khẩu"
           }
       ),
   )

   def get_invalid_login_error(self):
       return forms.ValidationError(
           "Tên đăng nhập hoặc mật khẩu không chính xác",
           code='invalid_login'
       )
