from functools import wraps

from cache_address_app.models import CachedAddress


def use_db_cache(func):
    @wraps(func)
    def with_cache(api_key: str, address: str):
        address = address.upper()

        try:
            cached_address = CachedAddress.objects.get(address=address)
            return cached_address.lng, cached_address.lat if cached_address.valid else None
        except CachedAddress.DoesNotExist:
            geodata = func(api_key, address)

            if geodata:
                lng, lat = geodata
                CachedAddress.objects.create(address=address, lng=lng, lat=lat, valid=True)
                return lng, lat
            else:
                CachedAddress.objects.create(address=address, valid=False)
                return

    return with_cache
