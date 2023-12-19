import time

from sanic import Blueprint
from torpedo import send_response, Request
from app.managers.diagnoBot import DiagnoBotManager
from app.routes.end_user.wrapper import http_v4_wrapper
from sanic import Request, Websocket


diagnoBot = Blueprint('diagnoBot')


@diagnoBot.route('/chat', methods=['POST'])
@http_v4_wrapper
async def get_diagnobot_response(request: Request, headers: dict):
    payload = request.custom_json()
    return await DiagnoBotManager().get_diagnobot_response(payload)


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

