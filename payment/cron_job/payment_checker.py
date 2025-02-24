from django.conf import settings
from django.db import transaction
from payment.models import Payment, Type
from adminapp.models import Config
from payment.utils import PaymentProcessor
import logging

logger = logging.getLogger(__name__)

class PaymentChecker:
    def __init__(self, payos_service):
        self.payos = payos_service

    def _get_or_create_config(self):
        config = Config.objects.first()
        if not config:
            config = Config.objects.create(
                total=0,
                per_month_price=settings.PER_MONTH_PRICE if settings.PER_MONTH_PRICE else 50000,
            )
            logger.info("Created new config")
        return config

    def process_pending_payment(self, payment):
        try:
            payment_info = self.payos.getPaymentLinkInformation(orderId=payment.order_id)

            if payment_info.status != "PAID":
                logger.info(f"Payment {payment.order_id} is not paid yet")
                return False

            with transaction.atomic():
                if payment.status:
                    logger.info(f"Payment {payment.order_id} already processed")
                    return True

                if int(payment_info.amount) != payment.amount:
                    logger.error(f"Amount mismatch for order {payment.order_id}: expected {payment.amount}, got {payment_info.amount}")
                    return False

                payment.status = True
                payment.save()
                logger.info(f"Updated payment status for order {payment.order_id}")

                config = self._get_or_create_config()
                config.total += payment.amount
                config.save()
                logger.info(f"Updated total amount in config: {config.total}")

                if payment.type == Type.MONTHLY_FUND.value:
                    processor = PaymentProcessor(None, payment.order_id, self.payos)
                    processor._process_monthly_fund(payment, config)

                return True

        except Exception as e:
            logger.error(f"Error processing payment {payment.order_id}: {str(e)}")
            return False

    def check_pending_payments(self):
        pending_payments = Payment.objects.filter(status=False)
        logger.info(f"Found {pending_payments.count()} pending payments to check")

        success_count = 0
        for payment in pending_payments:
            try:
                if self.process_pending_payment(payment):
                    success_count += 1
            except Exception as e:
                logger.error(f"Error checking payment {payment.order_id}: {str(e)}")
                continue

        logger.info(f"Successfully processed {success_count} out of {pending_payments.count()} pending payments")
        return success_count