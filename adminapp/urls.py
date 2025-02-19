from django.urls import path
from . import views

app_name = 'adminapp'

urlpatterns = [
    path('accounts/login/', views.UserLoginView.as_view(), name='login'),
    path('accounts/logout/', views.logout_view, name='logout'),
]