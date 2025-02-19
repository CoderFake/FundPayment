from django.db import models
from uuid import uuid4
from account.models import Account


class Type(models.TextChoices):
    MONTHLY_FUND = "monthly_fund", "Đóng quỹ tháng"
    DONATE = "donate", "Donate"


class PaymentType(models.TextChoices):
    MONTHLY_FUND = "monthly_fund", "Đóng quỹ tháng"
    DONATE = "donate", "Donate"
    ACTIVITIES_PAYMENT = "activities_payment", "Thanh toán hoạt động"


class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    order_id = models.CharField(max_length=100, unique=True, null=True, blank=True, verbose_name="Mã đơn hàng")
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="payments", null=True, blank=True)
    type = models.CharField(max_length=50, choices=PaymentType.choices, null=True, blank=True, verbose_name="Loại thanh toán")
    amount = models.IntegerField(verbose_name="Số tiền")
    description = models.TextField(verbose_name="Mô tả")
    status = models.BooleanField(default=False, verbose_name="Trạng thái")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Thanh toán"
        verbose_name_plural = "Thanh toán"

    def __str__(self):
        return f"{self.order_id} - {self.account.name if self.account else 'N/A'}"


class Months(models.IntegerChoices):
    JANUARY = 1, "Tháng 1"
    FEBRUARY = 2, "Tháng 2"
    MARCH = 3, "Tháng 3"
    APRIL = 4, "Tháng 4"
    MAY = 5, "Tháng 5"
    JUNE = 6, "Tháng 6"
    JULY = 7, "Tháng 7"
    AUGUST = 8, "Tháng 8"
    SEPTEMBER = 9, "Tháng 9"
    OCTOBER = 10, "Tháng 10"
    NOVEMBER = 11, "Tháng 11"
    DECEMBER = 12, "Tháng 12"


class Fund(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    year = models.IntegerField(verbose_name="Năm")
    month = models.IntegerField(choices=Months.choices, verbose_name="Tháng")
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="funds")
    status = models.BooleanField(default=False, verbose_name="Trạng thái")
    description = models.TextField(null=True, blank=True, verbose_name="Mô tả")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")

    class Meta:
        ordering = ['-year', '-month']
        verbose_name = "Quỹ tháng"
        verbose_name_plural = "Quỹ tháng"
        unique_together = ['year', 'month', 'account']

    def __str__(self):
        return f"{self.account.name} - Tháng {self.month}/{self.year}"


