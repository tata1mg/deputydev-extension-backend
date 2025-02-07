from sanic import Blueprint

from .auth import auth
from .config_handler import config
from .repos import repos

blueprints = [repos, auth, config]
common_v1_bp = Blueprint.group(*blueprints, url_prefix="v1")
