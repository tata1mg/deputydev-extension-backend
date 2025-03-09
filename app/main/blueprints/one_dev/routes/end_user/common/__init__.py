from sanic import Blueprint

from .v1 import common_v1_bp

blueprints = [common_v1_bp]
common_bp = Blueprint.group(*blueprints, url_prefix="common")
