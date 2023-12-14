from sanic.blueprints import Blueprint

from app.routes.end_user.v1.reorder import test

blueprints_v1 = Blueprint.group(test, url_prefix="/v1")
