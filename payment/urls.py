from django.urls import path
from . import views
urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),

    path("payment", views.Checkout.as_view(), name="payment"),

    path("payment/transactions", views.PaymentTransaction.as_view(), name="transaction"),

    path('payment/history', views.FundStatusView.as_view(), name="payment_history"),

    path('payment/return-payment', views.PaymentReturnView.as_view(), name="return_payment"),
]