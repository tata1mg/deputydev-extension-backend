import time

from sanic import Blueprint, Websocket
from sanic.log import logger
from sanic_ext import validate
from torpedo import Request

from app.backend_common.utils.wrapper import http_v4_wrapper
from app.common.utils.headers import Headers
from app.main.blueprints.jiva.models.chat import ChatModel
from app.main.blueprints.jiva.services.bots.jiva import JivaManager

jiva = Blueprint("jiva", url_prefix="/jiva")


@jiva.route("/chat", methods=["POST"])
@http_v4_wrapper
@validate(json=ChatModel.ChatRequestModel)
async def get_diagnobot_response(request: Request, headers: Headers, **kwargs):
    payload = request.custom_json()
    response = await JivaManager().get_diagnobot_response(ChatModel.ChatRequestModel(**payload), headers)
    return response


@jiva.route("/initialize", methods=["GET"])
@http_v4_wrapper
async def show_boat(request: Request, headers: Headers):
    response = await JivaManager().show_boat_based_on_ab(headers)
    return response


@jiva.websocket("/feed")
async def feed(request: Request, ws: Websocket):
    while True:
        data = "hello!"
        logger.info("Sending: " + data)
        for i in range(0, 20):
            time.sleep(1)
            await ws.send(data)
        data = await ws.recv()
        logger.info("Received: " + data)
