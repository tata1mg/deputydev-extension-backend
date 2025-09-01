import aiohttp
from sanic import Sanic
from sanic.log import logger
from sanic_ext.extensions.openapi.builders import SpecificationBuilder

from app.backend_common.utils.sanic_wrapper.common_utils import CONFIG


# FIXME: needs refactoring
async def get_openapi_json_file(app: Sanic) -> None:
    """Generates OpenAPI Spec & pushes it to ADAM Service.

    Author: Vishal Khare <vishal.khare@1mg.com>

    Args:
        app (Sanic): Sanic app instance.
    """
    if app.debug:
        return

    config = CONFIG.config.get("ADAM") or {}
    if not config.get("IS_ENABLED"):
        logger.warning("Project OneDoc - Disabled")
        return
    if not config.get("SERVICE_KEY"):
        logger.warning("Project OneDoc - Service key found missing")
        return
    if not config.get("ENVIRONMENT"):
        logger.warning("Project OneDoc - Environment not specified")
        return

    data = SpecificationBuilder().build(app).serialize()
    _service_name = config.get("SERVICE_NAME")
    _service_hosts = config.get("SERVICE_HOSTS")
    _env = config.get("ENVIRONMENT")
    data["info"]["title"] = f"{_service_name} service API documentation (Automated method)"
    if _service_hosts:
        # When API gateway will be migrated to sanic,
        # _service_host can be defined in its config
        # so that no code is required to be changed here.
        for host in _service_hosts:
            data["servers"].append({"url": host})
    else:
        data["servers"] = None
    _onedoc_endpoint = config.get("HOST") + "/v1/file/openapi/ci"

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                url=_onedoc_endpoint,
                json={
                    "openapi": data,
                    "service_key": config.get("SERVICE_KEY"),
                },
            ) as response:
                _response = await response.json()
                if _response.get("status_code") != 200:
                    _error_message = (
                        f"Project OneDoc - {_response['error']['message']}"
                        if _response.get("error")
                        else "Project OneDoc - An unexpected error has occurred"
                    )
                    logger.warning(_error_message)
                else:
                    logger.info(
                        "Project OneDoc - OpenAPI specification successfully uploaded to OneDoc"  # noqa: E501
                    )
        except Exception as err:
            logger.warning(
                f"Failed to communicate with OneDoc ({_onedoc_endpoint}) ! Exception : {err}"  # noqa: E501
            )
