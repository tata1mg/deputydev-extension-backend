from sanic import Blueprint

from .code_gen import code_gen_bp
from .common import common_bp
from .history import history_bp

blueprints = [common_bp, code_gen_bp, history_bp]
one_dev_end_user_bp = Blueprint.group(*blueprints, url_prefix="end_user")
