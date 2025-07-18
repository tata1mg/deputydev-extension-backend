from sanic import Blueprint

from app.main.blueprints.deputy_dev.routes.end_user.v1.ab_analysis_routes import (
    ab_analysis,
)
from app.main.blueprints.deputy_dev.routes.end_user.v1.backfill_missed_data import (
    backfill,
)
from app.main.blueprints.deputy_dev.routes.end_user.v1.code_review import smart_code
from app.main.blueprints.deputy_dev.routes.end_user.v1.dashboard_routes import console
from app.main.blueprints.deputy_dev.routes.end_user.v1.onboarding import onboarding_bp
from app.main.blueprints.deputy_dev.routes.end_user.v1.setting import setting
from app.main.blueprints.deputy_dev.routes.end_user.v1.extension_code_review import extension_code_review
from app.main.blueprints.deputy_dev.routes.end_user.v1.extension_agents import agents

blueprints = [
    smart_code,
    onboarding_bp,
    ab_analysis,
    console,
    setting,
    backfill,
    extension_code_review,
    agents
]  # onboarding flows,

code_review_v1_bp = Blueprint.group(*blueprints, url_prefix="v1")
