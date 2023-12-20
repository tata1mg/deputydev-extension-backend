import time

from sanic import Blueprint
from sanic_ext import validate
from torpedo import Request
from app.managers.diagnoBot import DiagnoBotManager
from app.models.chat import ChatRequestModel
from app.routes.end_user.wrapper import http_v4_wrapper
from sanic import Websocket


diagnoBot = Blueprint('diagnoBot')


@diagnoBot.route('/chat', methods=['POST'])
@http_v4_wrapper
@validate(json=ChatRequestModel)
async def get_diagnobot_response(request: Request,  headers: dict, **kwargs):
    payload = request.custom_json()
    return await DiagnoBotManager().get_diagnobot_response(ChatRequestModel(**payload))


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

