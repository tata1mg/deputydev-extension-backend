from torpedo import CONFIG, BaseApiRequest


class Base(BaseApiRequest):
    """
    Base class for all inter service requests. Each method will return

    AsyncTaskResponse(self._data['data'],
                      meta=self._data.get('meta', None),
                      status_code=self._data['status_code'],
                      headers=headers)
    """

    _timeout = CONFIG.config["INTERSERVICE_TIMEOUT"]
