from sanic.blueprints import Blueprint

from app.routes.end_user.v1 import blueprints_v1

blueprints_end_user = Blueprint.group(blueprints_v1, url_prefix="/end_user")
