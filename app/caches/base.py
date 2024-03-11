from redis_wrapper.client import RedisCache

# from app.json_encoder import jsonable_encoder


class Base(RedisCache):
    _service_prefix = "merch_service"

    # @classmethod
    # async def mset_with_expire(cls, mapping: dict, expire: int = None):
    #     keys = list(mapping.keys())
    #     for index in range(0, len(keys), cls._mset_with_expire_max_keys_limit):
    #         batch_mapping = {}
    #         for key in keys[index : index + cls._mset_with_expire_max_keys_limit]:
    #             batch_mapping[key] = jsonable_encoder(mapping[key])
    #         await super().mset_with_expire(batch_mapping, expire)