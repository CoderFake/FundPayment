from .caches import config_manager
from .data_classes import CommonInfo


def common_info(request):
   config = config_manager.get_config()
   if not config:
       return {}
   return {k: v for k, v in vars(CommonInfo(**config)).items() if v is not None}