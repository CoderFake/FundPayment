import random
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from adminapp.models import Config
from payment.models import PaymentType, Payment


class PaymentAdmin(admin.ModelAdmin):
   list_display = ('order_id', 'get_account_name', 'type', 'amount', 'status', 'created_at')
   list_filter = ('type', 'status')
   search_fields = ('order_id', 'account__name', 'description')
   readonly_fields = ('id', 'created_at')
   list_per_page = 20
   fields = ('account', 'type', 'amount', 'status', 'description')

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

            try:
               obj.amount = self.clean_amount(obj.amount)
            except ValueError:
               raise ValidationError("Số tiền không hợp lệ")

            if not change:
               obj.order_id = int(str(timezone.now().strftime("%H%M%S%f")) + str(random.randint(10, 999)))

            super().save_model(request, obj, form, change)

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