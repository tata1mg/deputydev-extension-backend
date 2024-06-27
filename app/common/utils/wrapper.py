from torpedo import Request, send_response

from app.common.utils.headers import Headers


def http_v4_wrapper(func):
    async def wrapper(request: Request):
        headers = Headers(request.headers)
        response = await func(request, headers)
        return send_response(response.model_dump())

    return wrapper
