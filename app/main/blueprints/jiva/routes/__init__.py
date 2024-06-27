from sanic.blueprints import Blueprint

from app.main.blueprints.jiva.routes.end_user import end_user_bp

jiva_end_user_bp = Blueprint.group(end_user_bp, url_prefix="")
