from sanic.blueprints import Blueprint

from app.routes.end_user.v1.jiva import jiva

blueprints_v1 = Blueprint.group(jiva, url_prefix="/v1/jiva")
