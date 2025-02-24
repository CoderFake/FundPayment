from django.conf import settings
from payos import PayOS
import logging

logger = logging.getLogger(__name__)

try:
    payOS = PayOS(
        client_id=settings.PAYOS_CLIENT_ID,
        api_key=settings.PAYOS_API_KEY,
        checksum_key=settings.PAYOS_CHECKSUM_KEY
    )
    logger.info("payOS initialized successfully.")
except Exception as e:
    logger.error("Failed to initialize payOS: %s", e)

