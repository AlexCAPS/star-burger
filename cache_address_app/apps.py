from django.apps import AppConfig


class CacheAddressAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cache_address_app'

    requre_update_after = '1m'
