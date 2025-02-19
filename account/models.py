from django.db import models
from uuid import uuid4


class Account(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    username = models.CharField(max_length=50, unique=True, verbose_name="Username")
    name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Họ tên")
    email = models.EmailField(max_length=100, unique=True, blank=True, null=True, verbose_name="email")
    is_active = models.BooleanField(default=True, verbose_name="Trạng thái")
    created_at = models.DateTimeField(null=True, blank=True, verbose_name="Thời gian tạo")

    class Meta:
        verbose_name = 'Danh sách thành viên'
        verbose_name_plural = 'Danh sách thành viên'

    def __str__(self):
        return self.name