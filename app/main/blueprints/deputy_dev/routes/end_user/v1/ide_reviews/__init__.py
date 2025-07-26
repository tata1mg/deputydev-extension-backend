from sanic import Blueprint

from app.main.blueprints.deputy_dev.routes.end_user.v1.ide_reviews.agents import agents
from app.main.blueprints.deputy_dev.routes.end_user.v1.ide_reviews.code_review_http import ide_review
from app.main.blueprints.deputy_dev.routes.end_user.v1.ide_reviews.code_review_ws import ide_review_websocket
from app.main.blueprints.deputy_dev.routes.end_user.v1.ide_reviews.repos import repos
from app.main.blueprints.deputy_dev.routes.end_user.v1.ide_reviews.comments import comments

blueprints = [
    ide_review_websocket,
    repos,
    ide_review,
    comments,
    agents
]

ide_reviews_v1_bp = Blueprint.group(*blueprints, url_prefix="ide-reviews")
