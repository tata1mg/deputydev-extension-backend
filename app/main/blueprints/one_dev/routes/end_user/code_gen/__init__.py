from sanic import Blueprint

from .v1.blueprint import code_gen_v1_bp
from .v2.blueprint import code_gen_v2_bp

blueprints = [code_gen_v1_bp, code_gen_v2_bp]
code_gen_bp = Blueprint.group(*blueprints, url_prefix="code_gen")
