import time

from sanic import Blueprint, Websocket
from sanic_ext import validate
from torpedo import Request

from app.backend_common.utils.wrapper import http_v4_wrapper
from app.main.blueprints.jiva.models.chat import ChatModel
from app.main.blueprints.jiva.services.bots.diagnoBot import DiagnoBotManager

diagnoBot = Blueprint("diagnoBot")


@diagnoBot.route("/chat", methods=["POST"])
@http_v4_wrapper
@validate(json=ChatModel.ChatRequestModel)
async def get_diagnobot_response(request: Request, headers: dict, **kwargs):
    payload = request.custom_json()
    response = await DiagnoBotManager().get_diagnobot_response(ChatModel.ChatRequestModel(**payload))
    return response


@diagnoBot.websocket("/feed")
async def feed(request: Request, ws: Websocket):
    while True:
        data = "hello!"
        print("Sending: " + data)
        for i in range(0, 20):
            time.sleep(1)
            await ws.send(data)
        data = await ws.recv()
        print("Received: " + data)
