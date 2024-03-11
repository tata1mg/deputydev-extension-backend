from sanic.blueprints import Blueprint

from app.routes.end_user.v1.jiva import jiva
from app.routes.end_user.v1.smart_code_review import smart_code

blueprints_v1 = Blueprint.group(jiva, smart_code, url_prefix="/v1")
