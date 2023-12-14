import time

from sanic import Blueprint
from torpedo import send_response, Request
from app.routes.end_user.wrapper import http_v4_wrapper
from sanic import Request, Websocket


test = Blueprint('test')


@test.route('/ping', methods=['GET'])
@http_v4_wrapper
async def get_reorder_widget_data(request: Request, headers: dict):
    return "pong"


@test.websocket("/feed")
async def feed(request: Request, ws: Websocket):
    while True:
        data = "hello!"
        print("Sending: " + data)
        for i in range(0, 20):
            time.sleep(1)
            await ws.send(data)
        data = await ws.recv()
        print("Received: " + data)

