
from sanic import Blueprint

from .code_gen.code_gen_blueprint import code_gen_v2_bp
blueprints = [
    code_gen_v2_bp,
]
common_v2_bp = Blueprint.group(*blueprints, url_prefix="v2")
