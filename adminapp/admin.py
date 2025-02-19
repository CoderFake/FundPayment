from django.contrib.admin import AdminSite
from account.admin import AccountAdmin
from payment.admin import PaymentAdmin
from account.models import Account
from payment.models import Payment


class CustomAdminSite(AdminSite):
    def get_app_list(self, request):
        app_list = super().get_app_list(request)
        return app_list


admin_site = CustomAdminSite(name="admin")

admin_site.register(Account, AccountAdmin)
admin_site.register(Payment, PaymentAdmin)