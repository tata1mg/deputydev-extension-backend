from sanic import Blueprint

from .v1 import code_review_v1_bp

deputy_dev_end_user_bp = Blueprint.group(code_review_v1_bp, url_prefix="end_user")
