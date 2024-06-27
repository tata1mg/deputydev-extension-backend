from sanic.blueprints import Blueprint

from app.main.blueprints.jiva.routes.end_user.v1.jiva import jiva

jiva_v1_bp = Blueprint.group(jiva, url_prefix="/v1")
