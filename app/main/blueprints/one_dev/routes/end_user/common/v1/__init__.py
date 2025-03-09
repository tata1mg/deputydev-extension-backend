from sanic import Blueprint

from .auth import auth
from .config_handler import config
from .repos import repos
from .rerank import rerank

blueprints = [repos, auth, config, rerank]
common_v1_bp = Blueprint.group(*blueprints, url_prefix="v1")
