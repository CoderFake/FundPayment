import os
import random

from django.conf import settings
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from adminapp.models import Config
from payment.models import PaymentType, Payment
from payment.utils import PaymentProcessor
from payment.payos import payOS
from django.utils.html import format_html

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'get_account_name', 'type', 'amount', 'status', 'created_at', 'get_image')
    list_filter = ('type', 'status')
    search_fields = ('order_id', 'account__name', 'description')
    readonly_fields = ('id', 'created_at', 'get_image_preview')
    list_per_page = 20
    fields = ('account', 'type', 'amount', 'status', 'description', 'image', 'get_image_preview')

    def get_image(self, obj):
        if obj.image:
            return format_html(
                '<div class="text-center"><img src="{}" class="rounded-2" style="object-fit: cover;" width="40" height="40" /></div>',
                obj.image.url
            )
        return format_html('<div class="text-center">Không có ảnh</div>')

    get_image.short_description = 'Hình ảnh'

    def get_image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="300" height="300" style="object-fit: contain;" />', obj.image.url)
        return "Không có hình ảnh xen trước"
    get_image_preview.short_description = 'Xem trước hình ảnh'

    def get_account_name(self, obj):
        return obj.account.name if obj.account else 'N/A'

    get_account_name.short_description = 'Tên tài khoản'
    get_account_name.admin_order_field = 'account__name'

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('order_id',)
        return self.readonly_fields

    def clean_amount(self, amount_str):
        cleaned = str(amount_str)
        for char in [',', '.', 'VND', 'VNĐ', ' ']:
            cleaned = cleaned.replace(char, '')
        return int(cleaned)

    def save_model(self, request, obj, form, change):
        try:
            with transaction.atomic():
                if change:
                    old_payment = Payment.objects.get(id=obj.id)
                    old_amount = old_payment.amount
                    old_type = old_payment.type

                    if 'image' in form.changed_data:
                        if old_payment.image:
                            old_image_path = os.path.join(settings.MEDIA_ROOT, str(old_payment.image))
                            if os.path.isfile(old_image_path):
                                os.remove(old_image_path)

                    if old_payment.status != obj.status and old_payment.status == False and old_payment != PaymentType.ACTIVITIES_PAYMENT:
                        try:
                            PaymentProcessor(request, obj.order_id, payOS,
                                             path=reverse('admin:payment_payment_changelist')).process_payment()
                        except Exception as e:
                            raise ValidationError(f"Lỗi khi lưu thanh toán: {str(e)}")

                try:
                    obj.amount = self.clean_amount(obj.amount)
                except ValueError:
                    raise ValidationError("Số tiền không hợp lệ")

                if not change:
                    obj.order_id = int(str(timezone.now().strftime("%H%M%S%f")) + str(random.randint(10, 999)))

                super().save_model(request, obj, form, change)

                if obj.image:
                    file_ext = obj.image.name.split('.')[-1]
                    new_name = f'payments/{obj.order_id}.{file_ext}'
                    old_path = obj.image.path
                    new_path = os.path.join(settings.MEDIA_ROOT, new_name)
                    if old_path != new_path:
                        os.makedirs(os.path.dirname(new_path), exist_ok=True)
                        os.rename(old_path, new_path)
                        obj.image.name = new_name
                        obj.save()

                config = Config.objects.select_for_update().first()
                if config:
                    if change:
                        if old_type == PaymentType.ACTIVITIES_PAYMENT:
                            config.total += old_amount
                        else:
                            config.total -= old_amount

                        if obj.type == PaymentType.ACTIVITIES_PAYMENT:
                            config.total -= obj.amount
                        else:
                            config.total += obj.amount
                    else:
                        if obj.type == PaymentType.ACTIVITIES_PAYMENT:
                            config.total -= obj.amount
                        else:
                            config.total += obj.amount

                    config.save()

        except Exception as e:
            raise ValidationError(f"Lỗi khi lưu thanh toán: {str(e)}")


class FundAdmin(admin.ModelAdmin):
    list_display = ('get_account_name', 'year', 'month', 'status', 'created_at')
    list_filter = ('year', 'month', 'status', 'created_at')
    search_fields = ('account__name', 'description')
    readonly_fields = ('id', 'created_at')
    list_per_page = 20

    def get_account_name(self, obj):
        return obj.account.name

    get_account_name.short_description = 'Tên tài khoản'
    get_account_name.admin_order_field = 'account__name'
