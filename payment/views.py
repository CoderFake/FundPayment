import random
from django.contrib.sites.shortcuts import get_current_site
from django.db import transaction
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib import messages
from django.urls import reverse
from django.views import View
from payos import PaymentData, ItemData
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from django.views.generic import ListView
from django.utils import timezone
from django.db.models import Prefetch
from account.models import Account
from payment.models import Type, Fund, Payment, Months, PaymentType
from adminapp.models import Config
import logging
from payment.payos import payOS
from payment.utils import PaymentProcessor

logger = logging.getLogger(__name__)
class HomeView(View):
    template_name = "users/index.html"

    def get(self, request):
        accounts = Account.objects.filter(is_active=True).values(
            "username", "name"
        )
        return render(request, self.template_name, {"accounts": accounts})

    def post(self, request):
        accounts = Account.objects.filter(is_active=True).values(
            "username", "name"
        )
        username = request.POST.get("username")

        if username not in ["anonymous"] + [account["username"] for account in accounts]:
            messages.error(request, "Người dùng không tồn tại!")
            return redirect('home')

        request.session["username"] = username

        return redirect(f"{reverse('payment')}?username={username}")


class FundStatusView(ListView):
    template_name = 'users/payment/payment_history.html'
    model = Account
    context_object_name = 'accounts'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_year = self.request.GET.get('year', timezone.now().year)
        try:
            current_year = int(current_year)
        except (ValueError, TypeError):
            current_year = timezone.now().year

        years = list(range(timezone.now().year, 2100))

        context.update({
            'current_year': current_year,
            'years': years,
            'months': Months.choices
        })
        return context

    def get_queryset(self):
        year = self.request.GET.get('year', timezone.now().year)
        return Account.objects.filter(
            is_active=True
        ).prefetch_related(
            Prefetch(
                'funds',
                queryset=Fund.objects.filter(year=year),
                to_attr='year_funds'
            )
        )


class PaymentReturnView(View):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.payos_service = payOS

    def get(self, request, *args, **kwargs):
        processor = PaymentProcessor(request, request.GET.get("orderCode", ""), self.payos_service)
        return processor.process_payment()

class Checkout(APIView):
    permission_classes = (AllowAny,)
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'users/payment/payment.html'

    def get(self, request):
        username = request.query_params.get('username')
        if not username:
            messages.error(request, "Vui lòng chọn tên người dùng!")
            return redirect('home')

        order_id = int(str(timezone.now().strftime("%H%M%S%f")) + str(random.randint(10, 999)))
        request.session["order_id"] = order_id

        if username != "anonymous":
            try:
                account = Account.objects.get(username=username)
            except Account.DoesNotExist:
                messages.error(request, "Người dùng không tồn tại!")
                return redirect('home')

            paid_months = Fund.objects.filter(
                account=account,
                year=timezone.now().year,
                status=True
            ).count()

            remaining_months = list(range(1, 13 - paid_months))
            types = [{"value": type.value, "label": type.label} for type in Type]

            if not remaining_months:
                types = [{"value": Type.DONATE.value, "label": Type.DONATE.label}]

            config = Config.objects.first()

            context = {
                "username": username,
                "order_id": order_id,
                "types": types,
                "months": remaining_months,
                "per_month_price": f"{config.per_month_price:_.0f}".replace("_", ".") + " VNĐ"
            }
        else:
            config = Config.objects.first()

            context = {
                "username": username,
                "order_id": order_id,
                "per_month_price": f"{config.per_month_price:_.0f}".replace("_", ".") + " VNĐ"
            }

        return Response(context, template_name=self.template_name, status=200)

    def post(self, request):
        order_id = request.POST.get("order_id", "")
        price = request.POST.get("price", "")
        type = request.POST.get("type", "")
        description = request.POST.get("description", None)
        username = request.POST.get("username", "")

        if order_id != str(request.session.get("order_id", "")):
            messages.error(request, "Mã đơn hàng không hợp lệ!")
            return redirect(f"{reverse('payment')}?username={username}")

        if type not in [Type.DONATE.value, Type.MONTHLY_FUND.value]:
            logger.error("missing type")
            messages.error(request, "Không tồn tại lựa chọn!")
            return redirect(f"{reverse('payment')}?username={username}")

        try:
            price = int(price.split(" ")[0].replace(".", ""))
        except Exception as e:
            logger.error(e)
            messages.error(request, "Mệnh giá không hợp lệ!")
            return redirect(f"{reverse('payment')}?username={username}")

        account = None
        desc = None
        if username != "anonymous":
            try:
                account = Account.objects.get(username=username)
                if type == Type.MONTHLY_FUND.value:
                    desc = f"{account.username} đóng {price // settings.PER_MONTH_PRICE} tháng"
                    description = desc
                else:
                    desc = f"{account.username} donate quỹ"

            except Account.DoesNotExist:
                messages.error(request, "Người dùng không tồn tại!")
                return redirect('home')

        elif username == "anonymous":
            name = request.POST.get("name", "")
            desc = f"{name} - donate quỹ"
            if len(desc) > 25:
                messages.error(request, "Tên không được quá 10 ký tự!")
                return redirect(f"{reverse('payment')}?username={username}")

            if price > 10000000:
                messages.error(request, "Số tiền không được lớn hơn 10.000.000 VNĐ!")
                return redirect(f"{reverse('payment')}?username={username}")

        if not description:
            description = desc

        if len(desc) > 100:
            messages.error(request, "Nội dung nhập quá dài!")
            return redirect(f"{reverse('payment')}?username={username}")

        sid = transaction.savepoint()
        try:
            item = ItemData(name=desc, quantity=1, price=int(price))
            current_site = get_current_site(request)

            paymentData = PaymentData(
                orderCode=int(order_id),
                amount=int(price),
                description=desc,
                items=[item],
                cancelUrl=f"{current_site}/payment/return-payment",
                returnUrl=f"{current_site}/payment/return-payment"
            )

            payment_data = {
                'order_id': order_id,
                'type': type,
                'amount': price,
                'description': description,
                'status': False
            }
            if username != "anonymous":
                payment_data['account'] = account

            Payment.objects.create(**payment_data)

            payosCreateResponse = payOS.createPaymentLink(paymentData)

            transaction.savepoint_commit(sid)
            return redirect(payosCreateResponse.checkoutUrl)

        except Exception as e:
            transaction.savepoint_rollback(sid)
            logger.error(e)
            return redirect(f"{reverse('payment')}?username={username}")


class PaymentTransaction(View):
    template_name = 'users/payment/transactions.html'

    def get_context_data(self, username='all', payment_type='all'):
        accounts = Account.objects.filter(is_active=True).values(
            "username", "name"
        )

        transactions = Payment.objects.filter(status=True)

        if username and username not in ["all", "anonymous"]:
            transactions = transactions.filter(account__username=username)

        if username == "anonymous":
            transactions = transactions.filter(account=None)

        if payment_type and payment_type != "all":
            transactions = transactions.filter(type=payment_type)

        transactions = transactions.order_by('-created_at')

        config = Config.objects.first()
        current_balance = config.total if config else 0

        return {
            'balance': current_balance,
            'transactions': transactions,
            'accounts': accounts,
            'payment_types': PaymentType.choices,
            'selected_username': username,
            'selected_type': payment_type,
            'per_month_price': config.per_month_price if config else settings.PER_MONTH_PRICE
        }

    def get(self, request):
        username = request.GET.get('username', 'all')
        payment_type = request.GET.get('type', 'all')
        context = self.get_context_data(username, payment_type)
        return render(request, self.template_name, context)

    def post(self, request):
        username = request.POST.get('username', 'all')
        payment_type = request.POST.get('type', 'all')

        if payment_type not in ['all'] + [type.value for type in PaymentType]:
            messages.error(request, "Loại hình thanh toán không tồn tại!")
            return redirect(f"{reverse('transaction')}?username={username}&type=all")

        accounts = Account.objects.filter(is_active=True).values_list('username', flat=True)
        if username not in ['all', 'anonymous'] + list(accounts):
            messages.error(request, "Người dùng không tồn tại!")
            return redirect(f"{reverse('transaction')}?username=all&type={payment_type}")

        return redirect(f"{reverse('transaction')}?username={username}&type={payment_type}")