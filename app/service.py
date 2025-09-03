from deputydev_core.utils.config_manager import ConfigManager
from sanic import Blueprint

from app.backend_common.utils.error_handler import DDErrorHandler
from app.backend_common.utils.sanic_wrapper import SanicWrapper

ConfigManager.initialize()

from app.listeners import listeners  # noqa : E402
from app.main.blueprints.deputy_dev.routes.end_user import (  # noqa : E402
    deputy_dev_end_user_bp,
)
from app.main.blueprints.one_dev.routes.end_user import (  # noqa : E402
    one_dev_end_user_bp,
)

main_app_bp = Blueprint.group(deputy_dev_end_user_bp, one_dev_end_user_bp, url_prefix="/")

sanic_wrapper = SanicWrapper(blueprints=main_app_bp, listeners=listeners, error_handler=DDErrorHandler())
_app = sanic_wrapper.create_app()
if __name__ == "__main__":
    sanic_wrapper.run()
