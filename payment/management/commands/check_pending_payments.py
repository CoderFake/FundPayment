from django.core.management import BaseCommand
from django.utils import timezone
from payment.cron_job.payment_checker import PaymentChecker
from payment.payos import payOS
import logging
import traceback

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check and update pending payments status at midnight'

    def handle(self, *args, **kwargs):
        current_time = timezone.localtime()
        logger.info(f"{'='*50}")
        logger.info(f"Starting check_pending_payments job at {current_time}")

        try:
            logger.info("Initializing PaymentChecker...")
            checker = PaymentChecker(payOS)

            logger.info("Processing pending payments...")
            processed_count = checker.check_pending_payments()

            success_msg = f'Successfully processed {processed_count} pending payments at {current_time}'
            logger.info(success_msg)
            self.stdout.write(self.style.SUCCESS(success_msg))

        except Exception as e:
            error_msg = f"Error running check_pending_payments at {current_time}: {str(e)}"
            logger.error(error_msg)
            logger.error(f"Traceback: {traceback.format_exc()}")
            self.stdout.write(self.style.ERROR(error_msg))

        finally:
            logger.info(f"Finished check_pending_payments job at {timezone.localtime()}")
            logger.info(f"{'='*50}")