class CacheFactory:
    @staticmethod
    def create_cache(cache_type: str, *args, **kwargs):
        if cache_type == "memory":
            from .local_cache import ExpiringLocalCache

            return ExpiringLocalCache(*args, **kwargs)
        if cache_type == "redis":
            from .redis_cache import RedisCache

            return RedisCache()
        raise ValueError(f"Unknown cache type: {cache_type}")
