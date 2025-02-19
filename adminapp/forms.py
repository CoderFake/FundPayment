from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import UsernameField
from django import forms

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
       label=_("Password"),
       strip=False,
       widget=forms.PasswordInput(
           attrs={
               "class": "form-control",
               "placeholder": "Password"
           }
       ),
   )

   def get_invalid_login_error(self):
       return forms.ValidationError(
           "Tên đăng nhập hoặc mật khẩu không chính xác",
           code='invalid_login'
       )