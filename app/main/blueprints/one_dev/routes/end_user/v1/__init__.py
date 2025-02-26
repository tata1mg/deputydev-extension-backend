from sanic import Blueprint

from .auth import auth
from .code_gen import code_gen
from .config_handler import config
from .repos import repos
from .rerank import rerank

blueprints = [code_gen, repos, auth, config, rerank]
one_dev_v1_bp = Blueprint.group(*blueprints, url_prefix="v1")
