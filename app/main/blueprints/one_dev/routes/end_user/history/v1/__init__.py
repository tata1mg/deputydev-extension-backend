from sanic import Blueprint

from .history import history

blueprints = [history]
history_v1_bp = Blueprint.group(*blueprints, url_prefix="v1")
