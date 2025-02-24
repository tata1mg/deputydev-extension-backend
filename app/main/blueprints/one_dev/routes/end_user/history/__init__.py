from sanic import Blueprint

from .v1 import history_v1_bp

blueprints = [history_v1_bp]
history_bp = Blueprint.group(*blueprints, url_prefix="history")
