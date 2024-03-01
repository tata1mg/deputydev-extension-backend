from redis_wrapper import RegisterRedis
from torpedo import Host, CONFIG

from app.listeners import listeners
from app.routes import blueprints


if __name__ == "__main__":
    # config object will be dict representation of config.json read by the utility function in torpedo

    Host._listeners = listeners

    # register combined blueprint group here. these blueprints are defined in the routes
    # directory and has to be collected in init file otherwise route will end up with 404 error.
    Host._blueprint_group = blueprints
    RegisterRedis.register_redis_cache(CONFIG.config["REDIS_CACHE_HOSTS"])
    Host.run()
