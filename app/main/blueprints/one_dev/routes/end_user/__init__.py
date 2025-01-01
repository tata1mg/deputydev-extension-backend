from sanic import Blueprint

from .v1 import one_dev_v1_bp

one_dev_end_user_bp = Blueprint.group(one_dev_v1_bp, url_prefix="end_user")
