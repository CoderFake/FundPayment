from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect
from django.utils import timezone
from adminapp.models import Config
from payment.models import Fund, Payment, Type
import logging

logger = logging.getLogger(__name__)


class PaymentProcessor:
    def __init__(self, request, order_id, payos_service, path='home'):
        self.request = request
        self.payos = payos_service
        self.order_id = order_id
        self.path = path

    def _calculate_fund_periods(self, payment, config, start_month_value):
        months_can_pay = int(payment.amount // config.per_month_price)
        funds_to_create = []

        start_year = (start_month_value - 1) // 12
        start_month = ((start_month_value - 1) % 12) + 1

        for i in range(months_can_pay):
            current_month = start_month + i

            years_to_add = (current_month - 1) // 12
            actual_year = start_year + years_to_add
            actual_month = ((current_month - 1) % 12) + 1

            funds_to_create.append(Fund(
                year=actual_year,
                month=actual_month,
                account=payment.account,
                status=True,
                description=f"Đóng quỹ tháng {actual_month}/{actual_year}"
            ))

        return funds_to_create

    def _get_start_month(self, payment, latest_fund):
        current_date = timezone.now()

        if latest_fund:
            latest_month_value = latest_fund.year * 12 + latest_fund.month
            next_month_value = latest_month_value + 1

            next_month = (latest_fund.month % 12) + 1
            next_year = latest_fund.year + (1 if latest_fund.month == 12 else 0)
            logger.info(f"Người dùng cũ tiếp tục đóng quỹ từ tháng: {next_month}/{next_year}")
            return next_month_value

        if payment.account and payment.account.created_at:
            join_date = payment.account.created_at
            join_day = join_date.day

            if join_day <= 15:
                start_month_value = join_date.year * 12 + join_date.month
                logger.info(
                    f"Tài khoản {payment.account.username} gia nhập ngày {join_day}/{join_date.month}/{join_date.year} (trước ngày 15)")
                logger.info(f"  -> Bắt đầu đóng quỹ từ tháng: {join_date.month}/{join_date.year}")
            else:
                next_month = (join_date.month % 12) + 1
                next_year = join_date.year + (1 if join_date.month == 12 else 0)
                start_month_value = next_year * 12 + next_month
                logger.info(
                    f"Tài khoản {payment.account.username} gia nhập ngày {join_day}/{join_date.month}/{join_date.year} (sau ngày 15)")
                logger.info(f"  -> Bắt đầu đóng quỹ từ tháng: {next_month}/{next_year}")

            return start_month_value

        current_month_value = current_date.year * 12 + current_date.month
        current_day = current_date.day

        if current_day <= 15:
            logger.info(
                f"Không có thông tin tài khoản, thanh toán trước ngày 15, bắt đầu từ tháng hiện tại: {current_date.month}/{current_date.year}")
            return current_month_value
        else:
            next_month_value = current_month_value + 1
            next_month = (current_date.month % 12) + 1
            next_year = current_date.year + (1 if current_date.month == 12 else 0)
            logger.info(
                f"Không có thông tin tài khoản, thanh toán sau ngày 15, bắt đầu từ tháng sau: {next_month}/{next_year}")
            return next_month_value

    def _get_or_create_config(self):
        config = Config.objects.first()
        if not config:
            config = Config.objects.create(
                total=0,
                per_month_price=settings.PER_MONTH_PRICE if settings.PER_MONTH_PRICE else 50000,
            )
            logger.info("Created new config")
        return config

    def _process_monthly_fund(self, payment, config):
        months_can_pay = int(payment.amount // config.per_month_price)

        if months_can_pay <= 0:
            logger.error(f"Invalid months_can_pay for order {self.order_id}: {months_can_pay}")
            if self.request:
                messages.error(self.request, "Số tiền thanh toán không đủ cho 1 tháng!")
            return False

        latest_fund = Fund.objects.filter(
            account=payment.account,
            status=True
        ).order_by('-year', '-month').first()

        start_month_value = self._get_start_month(payment, latest_fund)
        funds_to_create = self._calculate_fund_periods(payment, config, start_month_value)

        funds_to_create_filtered = []
        for fund in funds_to_create:
            existing = Fund.objects.filter(
                year=fund.year,
                month=fund.month,
                account=payment.account
            ).exists()

            if not existing:
                funds_to_create_filtered.append(fund)
            else:
                logger.info(
                    f"Bỏ qua bản ghi quỹ đã tồn tại: tháng {fund.month}/{fund.year} cho tài khoản {payment.account.username}")

        if funds_to_create_filtered:
            Fund.objects.bulk_create(funds_to_create_filtered)
            logger.info(f"Created {len(funds_to_create_filtered)} fund records for order {self.order_id}")
        else:
            logger.info(f"No new fund records needed for order {self.order_id}")

        return True

    def process_payment(self):
        logger.info(f"Processing payment return for order: {self.order_id}")

        try:
            payment_info = self.payos.getPaymentLinkInformation(orderId=self.order_id)

            if payment_info.status != "PAID":
                messages.info(self.request, 'Thanh toán đã bị hủy!')
                return redirect(self.path)

            with transaction.atomic():
                try:
                    payment = Payment.objects.get(order_id=self.order_id)

                    if payment.status:
                        logger.info(f"Payment {self.order_id} already processed")
                        messages.success(self.request, "Thanh toán thành công!")
                        return self._redirect_based_on_type(payment.type)

                    if int(payment_info.amount) != payment.amount:
                        logger.error(
                            f"Amount mismatch for order {self.order_id}: expected {payment.amount}, got {payment_info.amount}")
                        messages.error(self.request, "Số tiền thanh toán không khớp!")
                        return redirect(self.path)

                    payment.status = True
                    payment.save()
                    logger.info(f"Updated payment status for order {self.order_id}")

                    config = self._get_or_create_config()
                    config.total += payment.amount
                    config.save()
                    logger.info(f"Updated total amount in config: {config.total}")

                    if payment.type == Type.MONTHLY_FUND.value:
                        if not self._process_monthly_fund(payment, config):
                            return redirect(self.path)

                    messages.success(self.request, "Thanh toán thành công!")
                    return self._redirect_based_on_type(payment.type)

                except Payment.DoesNotExist:
                    logger.error(f"Payment not found for order {self.order_id}")
                    messages.error(self.request, "Thanh toán không thành công, không tìm thấy mã đơn hàng!")
                    return redirect(self.path)

                except Exception as e:
                    logger.error(f"Error processing payment {self.order_id}: {str(e)}")
                    transaction.rollback()
                    messages.error(self.request, "Thanh toán không thành công!")
                    return redirect(self.path)

        except Exception as e:
            logger.error(f"Error getting payment information from PayOS for order {self.order_id}: {str(e)}")
            messages.error(self.request, "Không thể kết nối với cổng thanh toán!")
            return redirect(self.path)

    def _redirect_based_on_type(self, payment_type):
        return redirect('payment_history' if payment_type == Type.MONTHLY_FUND.value else 'transaction')