from sanic import Blueprint

from app.main.blueprints.deputy_dev.routes.end_user import deputy_dev_end_user_bp
from app.main.blueprints.jiva.routes import jiva_end_user_bp
from app.main.blueprints.one_dev.routes.end_user import one_dev_end_user_bp

main_app_bp = Blueprint.group(jiva_end_user_bp, deputy_dev_end_user_bp, one_dev_end_user_bp, url_prefix="/")
