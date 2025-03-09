from sanic import Blueprint

from .v1 import query_solver_v1_bp

blueprints = [query_solver_v1_bp]
query_solver_bp = Blueprint.group(*blueprints, url_prefix="query_solver")
