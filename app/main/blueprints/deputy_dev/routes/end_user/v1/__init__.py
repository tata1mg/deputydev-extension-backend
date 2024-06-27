from sanic import Blueprint

from app.main.blueprints.deputy_dev.routes.end_user.v1.code_review import smart_code

code_review_v1_bp = Blueprint.group(smart_code, url_prefix="v1")
