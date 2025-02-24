from deputydev_core.utils.config_manager import ConfigManager
from redis_wrapper import RegisterRedis
from sanic import Blueprint
from torpedo import CONFIG, Host

ConfigManager.initialize()

from app.listeners import listeners  # noqa : E402
from app.main.blueprints.deputy_dev.routes.end_user import (  # noqa : E402
    deputy_dev_end_user_bp,
)
from app.main.blueprints.jiva.routes import jiva_end_user_bp  # noqa : E402
from app.main.blueprints.one_dev.routes.end_user import (  # noqa : E402
    one_dev_end_user_bp,
)

main_app_bp = Blueprint.group(jiva_end_user_bp, deputy_dev_end_user_bp, one_dev_end_user_bp, url_prefix="/")


if __name__ == "__main__":
    # config object will be dict representation of config.json read by the utility function in torpedo

    Host._listeners = listeners
    Host._db_config = CONFIG.config["DB_CONNECTIONS"]

    # register combined blueprint group here. these blueprints are defined in the routes
    # directory and has to be collected in init file otherwise route will end up with 404 error.
    Host._blueprint_group = main_app_bp
    RegisterRedis.register_redis_cache(CONFIG.config["REDIS_CACHE_HOSTS"])
    Host.run()
