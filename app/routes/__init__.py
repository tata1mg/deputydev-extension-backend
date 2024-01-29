from sanic.blueprints import Blueprint

from app.routes.end_user import blueprints_end_user

blueprints = Blueprint.group(blueprints_end_user, url_prefix="")
