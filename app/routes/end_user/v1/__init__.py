from sanic.blueprints import Blueprint

from app.routes.end_user.v1.diagnoBot import diagnoBot

blueprints_v1 = Blueprint.group(diagnoBot, url_prefix="/v1")
