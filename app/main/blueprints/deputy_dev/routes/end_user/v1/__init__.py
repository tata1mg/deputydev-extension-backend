from sanic import Blueprint

from app.main.blueprints.deputy_dev.routes.end_user.v1.ab_analysis_routes import (
    ab_analysis,
)
from app.main.blueprints.deputy_dev.routes.end_user.v1.code_review import smart_code
from app.main.blueprints.deputy_dev.routes.end_user.v1.dashboard_routes import console
from app.main.blueprints.deputy_dev.routes.end_user.v1.ide_reviews import ide_reviews_v1_bp
from app.main.blueprints.deputy_dev.routes.end_user.v1.onboarding import onboarding_bp
from app.main.blueprints.deputy_dev.routes.end_user.v1.setting import setting

blueprints = [
    smart_code,
    onboarding_bp,
    ab_analysis,
    console,
    setting,
    ide_reviews_v1_bp,
]  # onboarding flows,

code_review_v1_bp = Blueprint.group(*blueprints, url_prefix="v1")
