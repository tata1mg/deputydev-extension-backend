
from sanic import Sanic
from torpedo import Host
from torpedo.common_utils import CONFIG
from redis_wrapper import RegisterRedis

async def setup_test(loop, sanic_client, app, blueprint_group):
    """
    helper method for setting up test
    :param loop:
    :param sanic_client:
    :param app:
    :param blueprint_group:
    :return:
    """
    Sanic.test_mode = True
    Host._blueprint_group = blueprint_group

    Host._config = CONFIG.config
    Host.setup_host()
    # update app config from config.json from service directory
    app.update_config(Host._config)

    # register mongodb
    # await Driver.register_test_db(app, loop)

    Host.setup_app_ctx(app)
    Host._db_config = CONFIG.config["TEST_DB_CONNECTIONS"]
    Host.register_databases(app)

    Host.register_listeners(app)
    Host.register_middlewares(app)
    Host.register_exception_handler(app)
    Host.register_app_blueprints(app)
    Host.setup_dynamic_methods()
    RegisterRedis.register_redis_cache(CONFIG.config["REDIS_CACHE_HOSTS"])
   

    _cli = await loop.create_task(sanic_client(app))
    return _cli
