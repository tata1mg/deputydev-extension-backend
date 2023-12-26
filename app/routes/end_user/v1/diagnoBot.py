import time

from sanic import Blueprint
from sanic_ext import validate
from torpedo import Request
from app.managers.diagnoBot import DiagnoBotManager
from app.models.chat import ChatModel
from app.routes.end_user.wrapper import http_v4_wrapper
from sanic import Websocket


diagnoBot = Blueprint("diagnoBot")


@diagnoBot.route("/chat", methods=["POST"])
@http_v4_wrapper
@validate(json=ChatModel.ChatRequestModel)
async def get_diagnobot_response(request: Request, headers: dict, **kwargs):
    payload = request.custom_json()
    response = await DiagnoBotManager().get_diagnobot_response(
        ChatModel.ChatRequestModel(**payload)
    )
    return response

# TODO : ADAM integration
# TODO : Test cases
# TODO : Bitbucket pipeline creation
# TODO : Explore websocket API
# TODO : How to ingest price of lab tests?
# TODO : Ingest all docs in pre-stag DB after running `CREATE EXTENSION vector`
# TODO : How to recommend lab test to someone?
# TODO : Change response format to entertain type. Type can be text of lab test card etc.
# TODO : Front end development
# TODO : pre-stag deployment of service.
# TODO : How to handle context where chat_history comes in to play?
# TODO : Validation - If current_prompt is present in payload then chat_id should also be present and vice-versa.
# TODO : Change response model to have type key.


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
