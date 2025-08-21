from app.backend_common.utils.sanic_wrapper import CONFIG, BaseAPIClient


class Base(BaseAPIClient):
    """
    Base class for all inter service requests. Each method will return

    AsyncTaskResponse(self._data['data'],
                      meta=self._data.get('meta', None),
                      status_code=self._data['status_code'],
                      headers=headers)
    """

    _timeout = CONFIG.config["INTERSERVICE_TIMEOUT"]
