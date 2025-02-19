from functools import lru_cache
from adminapp.models import Config


class ConfigurationManager:
    def __init__(self):
        self._config = None

    @lru_cache(maxsize=1)
    def _get_config_from_db(self):
        try:
            config = Config.objects.first()
            if not config:
                return None

            return {
                'BUSINESS_UNIT': config.business_unit,
                'CONTACT_EMAIL': config.email_contact,
                'CONTACT_PHONE': config.phone_contact,
                'FOOTER_TEXT': config.footer_text,
                'LOGO_URL': config.logo_url,
                'FAVICON_URL': config.favicon_url,
                'SLOGAN': config.slogan
            }
        except Exception:
            return None

    def get_config(self):
        config = self._get_config_from_db()
        if config is None:
            self._get_config_from_db.cache_clear()
            config = self._get_config_from_db()
        return config


config_manager = ConfigurationManager()