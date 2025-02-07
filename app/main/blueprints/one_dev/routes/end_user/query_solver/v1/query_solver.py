from sanic import Blueprint
from torpedo import Request
from sanic.response import stream


query_solver = Blueprint("query_solver", "/")

@code_gen.route("/solve-user-query")
async def solve_user_query(_request: Request, auth_data: AuthData, **kwargs):
    response = await _request.respond()
    async def sample_streaming_fn(response):
        response.write('foo,')
        response.write('bar')
    return stream(sample_streaming_fn, content_type='text/event-stream')
