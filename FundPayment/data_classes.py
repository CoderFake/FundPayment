from dataclasses import dataclass
from typing import Optional

@dataclass
class CommonInfo:
   BUSINESS_UNIT: str = 'BU2'
   CONTACT_EMAIL: Optional[str] = None
   CONTACT_PHONE: Optional[str] = None
   FOOTER_TEXT: Optional[str] = None
   LOGO_URL: Optional[str] = None
   ADMIN_LOGO_URL: Optional[str] = None
   FAVICON_URL: Optional[str] = None
   SLOGAN: Optional[str] = None