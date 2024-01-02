import time

from sanic import Blueprint
from sanic_ext import validate
from torpedo import Request, send_response
from app.managers.diagnoBot import DiagnoBotManager
from app.models.chat import ChatModel
from app.routes.end_user.wrapper import http_v4_wrapper
from app.routes.end_user.headers import Headers
from sanic import Websocket


diagnoBot = Blueprint("diagnoBot")


@diagnoBot.route("/chat", methods=["POST"])
@http_v4_wrapper
@validate(json=ChatModel.ChatRequestModel)
async def get_diagnobot_response(request: Request, headers: Headers, **kwargs):
    payload = request.custom_json()
    response = await DiagnoBotManager().get_diagnobot_response(
        ChatModel.ChatRequestModel(**payload), headers
    )
    return response


# TODO : ADAM integration
# TODO : Test cases
# TODO : Bitbucket pipeline creation
# TODO : Explore websocket API
# TODO : Ingest all docs in pre-stag DB after running `CREATE EXTENSION vector`
# TODO : Front end development
# TODO : pre-stag deployment of service.
# TODO : Validation - If current_prompt is present in payload then chat_id should also be present and vice-versa.
# TODO : Create an NPS survey 4-5 (Promoters), 3 (Passives), 2-1 (Detractors)


@diagnoBot.route("/showboat", methods=["GET"])
@http_v4_wrapper
async def show_boat(request: Request, headers: Headers):
    response = await DiagnoBotManager().show_boat_based_on_ab(headers)
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
