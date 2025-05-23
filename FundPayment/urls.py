"""
URL configuration for FundPayment project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.views.static import serve
from django.conf.urls.static import static
from adminapp.admin import admin_site
from django.urls import path, include, re_path
from .caches import config_manager


def get_admin_path():
   config = config_manager.get_config()
   if config and config.get('BUSINESS_UNIT'):
       return f"{config['BUSINESS_UNIT'].replace(' ', '').lower()}/admin/"
   return "admin/"

urlpatterns = [
   path(get_admin_path(), include("adminapp.urls")),

   path(get_admin_path(), admin_site.urls),
   path("", include("payment.urls")),

   re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)