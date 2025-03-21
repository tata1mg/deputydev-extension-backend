from sanic import Blueprint

from .v1 import common_v1_bp
from .v2 import common_v2_bp

blueprints = [common_v1_bp, common_v2_bp]
one_dev_end_user_bp = Blueprint.group(*blueprints, url_prefix="end_user")
