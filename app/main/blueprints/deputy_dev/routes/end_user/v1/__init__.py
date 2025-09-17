from sanic import Blueprint

from app.main.blueprints.deputy_dev.routes.end_user.v1.ide_reviews import ide_reviews_v1_bp

blueprints = [
    ide_reviews_v1_bp,
]  # onboarding flows,

code_review_v1_bp = Blueprint.group(*blueprints, url_prefix="v1")
