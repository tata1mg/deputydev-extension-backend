from sanic import Blueprint

from app.main.blueprints.deputy_dev.routes.end_user.v1.ab_analysis_routes import (
    ab_analysis,
)
from app.main.blueprints.deputy_dev.routes.end_user.v1.code_review import smart_code
from app.main.blueprints.deputy_dev.routes.end_user.v1.onboarding import onboarding_bp

blueprints = [smart_code, onboarding_bp, ab_analysis]  # onboarding flows,

code_review_v1_bp = Blueprint.group(*blueprints, url_prefix="v1")
