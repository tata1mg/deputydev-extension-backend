from sanic import Blueprint

from .v1 import code_gen_v1_bp


blueprints = [code_gen_v1_bp]
code_gen_bp = Blueprint.group(*blueprints, url_prefix="code_gen")
