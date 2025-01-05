from sanic import Blueprint

from .auth import auth
from .code_gen import code_gen
from .config_handler import config
from .repos import repos

blueprints = [code_gen, repos, auth, config]
one_dev_v1_bp = Blueprint.group(*blueprints, url_prefix="v1")
