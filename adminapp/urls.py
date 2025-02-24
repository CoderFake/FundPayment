from django.urls import path
from . import views

app_name = 'adminapp'

urlpatterns = [
    path('login/', views.UserLoginView.as_view(), name='admin_login'),
    path('logout/', views.logout_view, name='admin_logout'),
    path('dashboard/', views.IndexView.as_view(), name='dashboard'),
    path('accounts/register/', views.register, name='register'),

    #api
    path('api/summary-dashboard/', views.DashboardSummaryAPIView.as_view(), name='summary_dashboard'),
    path('api/payment-distribution-dashboard/', views.DashboardPaymentDistributionAPIView.as_view(), name='payment_distribution_dashboard'),
    path('api/payment-dashboard/', views.DashboardPaymentAPIView.as_view(), name='payment_dashboard'),
    path('api/fund-status-dashboard/', views.DashboardFundStatus.as_view(), name='fund_status_dashboard'),
]