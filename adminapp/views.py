from admin_soft.forms import RegistrationForm, UserPasswordResetForm, UserSetPasswordForm
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import When, Value, CharField, Case, Count, Sum, Q, Prefetch
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from account.models import Account
from payment.models import PaymentType, Payment, Fund, Months
from .decorators import user_is_staff
from .forms import LoginForm
from django.contrib.auth import logout
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordResetConfirmView
from django.shortcuts import redirect, render


class IndexView(LoginRequiredMixin, View):
    template_name = 'pages/dashboard.html'
    login_url = reverse_lazy('adminapp:admin_login')

    def get(self, request):
        return render(request, self.template_name, {'segment': 'dashboard'})


class UserLoginView(LoginView):
    template_name = 'admin/login.html'
    form_class = LoginForm

    success_url = reverse_lazy('adminapp:dashboard')

    def form_invalid(self, form):
        messages.error(
            self.request,
            "Tên đăng nhập hoặc mật khẩu không chính xác"
        )
        return super().form_invalid(form)

    def get_success_url(self):
        return self.success_url


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            print('Account created successfully!')
            return redirect(reverse('adminapp:admin_login'))
        else:
            print("Register failed!")
    else:
        form = RegistrationForm()

    context = {'form': form}
    return render(request, 'accounts/register.html', context)


def logout_view(request):
    logout(request)
    return redirect(reverse('adminapp:admin_login'))


class UserPasswordResetView(PasswordResetView):
    template_name = 'accounts/password_reset.html'
    form_class = UserPasswordResetForm


class UserPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'accounts/password_reset_confirm.html'
    form_class = UserSetPasswordForm



class DashboardSummaryAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        current_year = timezone.now().year
        last_year = current_year - 1

        current_members = Account.objects.filter(is_active=True).count()
        last_year_members = Account.objects.filter(
            is_active=True,
            created_at__year__lte=last_year
        ).count()
        member_growth = self.calculate_growth(current_members, last_year_members)


        current_balance = Payment.objects.filter(
            status=True,
            created_at__year=current_year
        ).aggregate(
            income=Sum('amount', filter=Q(
                type__in=[PaymentType.MONTHLY_FUND, PaymentType.DONATE]
            )) or 0,
            expense=Sum('amount', filter=Q(
                type=PaymentType.ACTIVITIES_PAYMENT
            )) or 0
        )
        current_fund = (current_balance['income'] or 0) - (current_balance['expense'] or 0)

        last_year_balance = Payment.objects.filter(
            status=True,
            created_at__year=last_year
        ).aggregate(
            income=Sum('amount', filter=Q(
                type__in=[PaymentType.MONTHLY_FUND, PaymentType.DONATE]
            )) or 0,
            expense=Sum('amount', filter=Q(
                type=PaymentType.ACTIVITIES_PAYMENT
            )) or 0
        )
        last_year_fund = (last_year_balance['income'] or 0) - (last_year_balance['expense'] or 0)
        fund_growth = self.calculate_growth(current_fund, last_year_fund)

        # Tính tổng thu
        current_income = current_balance['income'] or 0
        last_year_income = last_year_balance['income'] or 0
        income_growth = self.calculate_growth(current_income, last_year_income)

        # Tính tổng chi
        current_expense = current_balance['expense'] or 0
        last_year_expense = last_year_balance['expense'] or 0
        expense_growth = self.calculate_growth(current_expense, last_year_expense)

        return Response({
            'members': {
                'current': current_members,
                'previous': last_year_members,
                'growth': member_growth
            },
            'current_fund': {
                'current': current_fund,
                'previous': last_year_fund,
                'growth': fund_growth
            },
            'total_income': {
                'current': current_income,
                'previous': last_year_income,
                'growth': income_growth
            },
            'total_expense': {
                'current': current_expense,
                'previous': last_year_expense,
                'growth': expense_growth
            }
        })

    def calculate_growth(self, current, previous):
        if previous == 0:
            return 100 if current > 0 else 0
        return round(((current - previous) / previous) * 100, 1)


class DashboardPaymentDistributionAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        current_date = timezone.now()
        year = int(request.GET.get('year', current_date.year))
        view_type = request.GET.get('view_type', 'year')

        base_query = Payment.objects.filter(
            created_at__year=year,
            status=True
        )

        if view_type == 'month':
            month = int(request.GET.get('month', current_date.month))
            base_query = base_query.filter(created_at__month=month)

        stats = base_query.aggregate(
            monthly_fund=Sum('amount', filter=Q(type=PaymentType.MONTHLY_FUND)),
            donate=Sum('amount', filter=Q(type=PaymentType.DONATE)),
            activities_payment=Sum('amount', filter=Q(type=PaymentType.ACTIVITIES_PAYMENT))
        )

        return Response({
            'monthly_fund': stats['monthly_fund'] or 0,
            'donate': stats['donate'] or 0,
            'activities_payment': stats['activities_payment'] or 0
        })


class DashboardPaymentAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        current_date = timezone.now()
        year = int(request.GET.get('year', current_date.year))
        month = int(request.GET.get('month', current_date.month))

        # Lấy dữ liệu theo tháng hiện tại hoặc được chọn
        monthly_data = Payment.objects.filter(
            created_at__year=year,
            created_at__month=month,
            status=True
        ).aggregate(
            current_income=Sum('amount', filter=Q(
                type__in=[PaymentType.MONTHLY_FUND, PaymentType.DONATE]
            )),
            current_expense=Sum('amount', filter=Q(
                type=PaymentType.ACTIVITIES_PAYMENT
            ))
        )

        # Xử lý trường hợp không có dữ liệu
        current_income = monthly_data['current_income'] or 0
        current_expense = monthly_data['current_expense'] or 0
        current_balance = current_income - current_expense

        # Lấy dữ liệu theo năm được chọn
        yearly_data = Payment.objects.filter(
            created_at__year=year,
            status=True
        ).aggregate(
            total_income=Sum('amount', filter=Q(
                type__in=[PaymentType.MONTHLY_FUND, PaymentType.DONATE]
            )),
            total_expense=Sum('amount', filter=Q(
                type=PaymentType.ACTIVITIES_PAYMENT
            ))
        )

        total_income = yearly_data['total_income'] or 0
        total_expense = yearly_data['total_expense'] or 0
        yearly_balance = total_income - total_expense

        monthly_stats = []
        for m in range(1, 13):
            month_data = Payment.objects.filter(
                created_at__year=year,
                created_at__month=m,
                status=True
            ).aggregate(
                total_income=Sum('amount', filter=Q(
                    type__in=[PaymentType.MONTHLY_FUND, PaymentType.DONATE]
                )),
                expense=Sum('amount', filter=Q(
                    type=PaymentType.ACTIVITIES_PAYMENT
                ))
            )

            month_data['month'] = m
            month_data['total_income'] = month_data['total_income'] or 0
            month_data['expense'] = month_data['expense'] or 0
            monthly_stats.append(month_data)

        return Response({
            'current': {
                'year': year,
                'month': month,
                'income': current_income,
                'expense': current_expense,
                'balance': current_balance
            },
            'yearly': {
                'year': year,
                'income': total_income,
                'expense': total_expense,
                'balance': yearly_balance
            },
            'monthly_stats': monthly_stats
        })


class PaymentHistoryAPIView(APIView):
    @user_is_staff
    def get(self, request):
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))

        payment_category = request.GET.get('category')
        payment_type = request.GET.get('type')

        payments = Payment.objects.all()

        if payment_category == 'income':
            payments = payments.filter(type__in=[PaymentType.MONTHLY_FUND, PaymentType.DONATE])
        elif payment_category == 'expense':
            payments = payments.filter(type=PaymentType.ACTIVITIES_PAYMENT)
        elif payment_type:
            payments = payments.filter(type=payment_type)

        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        if start_date and end_date:
            payments = payments.filter(created_at__range=[start_date, end_date])

        total = payments.count()
        payments = payments[(page - 1) * page_size:page * page_size]

        payment_list = payments.values(
            'order_id',
            'account__name',
            'type',
            'amount',
            'description',
            'status',
            'created_at'
        ).annotate(
            category=Case(
                When(type__in=[PaymentType.MONTHLY_FUND, PaymentType.DONATE], then=Value('income')),
                When(type=PaymentType.ACTIVITIES_PAYMENT, then=Value('expense')),
                output_field=CharField(),
            )
        )

        return Response({
            'total': total,
            'page': page,
            'page_size': page_size,
            'results': payment_list
        })


class DashboardFundStatus(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        current_year = timezone.now().year
        year = request.GET.get('year', current_year)

        try:
            year = int(year)
        except (ValueError, TypeError):
            year = current_year

        accounts = Account.objects.filter(
            is_active=True
        ).prefetch_related(
            Prefetch(
                'funds',
                queryset=Fund.objects.filter(year=year),
                to_attr='year_funds'
            )
        )

        account_data = []
        for account in accounts:
            fund_status = {}
            for fund in account.year_funds:
                fund_status[fund.month] = {
                    'status': fund.status,
                    'created_at': fund.created_at
                }

            account_data.append({
                'id': account.id,
                'name': account.name,
                'username': account.username,
                'email': account.email,
                'fund_status': fund_status
            })

        return Response({
            'current_year': year,
            'years': list(range(current_year, 2100)),
            'months': dict(Months.choices),
            'accounts': account_data
        })