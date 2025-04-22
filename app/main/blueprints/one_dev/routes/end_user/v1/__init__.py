from sanic import Blueprint

from .auth.auth_blueprint import auth_v1_bp
from .chunks.chunks_blueprint import chunks_v1_bp
from .code_gen.code_gen_blueprint import code_gen_v1_bp
from .configs.config_blueprint import config_v1_bp
from .history.history_blueprint import history_v1_bp
from .repos.repos_blueprint import repos_v1_bp
from .ui_data.ui_data_blueprint import ui_data_v1_bp
from .websocket_connection.websocket_connection_blueprint import (
    websocket_connection_v1_bp,
)
from .urls.urls_blueprint import urls_v1_bp

blueprints = [
    auth_v1_bp,
    config_v1_bp,
    history_v1_bp,
    repos_v1_bp,
    code_gen_v1_bp,
    chunks_v1_bp,
    ui_data_v1_bp,
    websocket_connection_v1_bp,
    urls_v1_bp,
]
common_v1_bp = Blueprint.group(*blueprints, url_prefix="v1")
