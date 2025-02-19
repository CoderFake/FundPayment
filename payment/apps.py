from django.apps import AppConfig


class PaymentConfig(AppConfig):
    default_auto_field = "django.shell.models.BigAutoField"
    name = "payment"
    verbose_name = "Quản lý thanh toán"
