from django.contrib.auth.models import AbstractUser
from django.db import models
from uuid import uuid4


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='adminapp_user_set',
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='adminapp_user_set',
        blank=True,
    )

    class Meta:
        verbose_name = 'Danh sách quản lý'
        verbose_name_plural = 'Danh sách quản lý'

    def __str__(self):
        return self.username


class Config(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    business_unit = models.CharField(max_length=50, verbose_name="Tên tổ chức")
    email_contact = models.CharField(max_length=50, verbose_name="Email liên hệ")
    phone_contact = models.CharField(max_length=20, verbose_name="Số điện thoại liên hệ")
    footer_text = models.CharField(max_length=255, verbose_name="Tên chân trang")
    logo_url = models.CharField(max_length=1000, verbose_name="Đường dẫn logo")
    favicon_url = models.CharField(max_length=1000, verbose_name="Đường dẫn favicon")
    slogan = models.CharField(max_length=1000, verbose_name="Slogan")
    total = models.IntegerField(default=0, verbose_name="Tổng số dư")
    per_month_price = models.IntegerField(default=50000, verbose_name="Số tiền đóng quỹ/tháng")

    class Meta:
        verbose_name = 'Cấu hình chung'
        verbose_name_plural = 'Cấu hình chung'


class Migration(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(unique=True, max_length=255)
    hash = models.CharField(unique=True, max_length=255)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
