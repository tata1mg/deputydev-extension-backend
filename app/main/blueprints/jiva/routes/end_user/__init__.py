from sanic.blueprints import Blueprint

from .v1 import jiva_v1_bp

end_user_bp = Blueprint.group(jiva_v1_bp, url_prefix="/end_user")
