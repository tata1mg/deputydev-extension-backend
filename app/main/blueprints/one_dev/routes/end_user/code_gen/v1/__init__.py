from sanic import Blueprint

from .code_gen import code_gen
blueprints = [code_gen]
code_gen_v1_bp = Blueprint.group(*blueprints, url_prefix="v1")
