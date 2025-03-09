from sanic import Blueprint

from .query_solver import query_solver

blueprints = [query_solver]
query_solver_v1_bp = Blueprint.group(*blueprints, url_prefix="v1")
