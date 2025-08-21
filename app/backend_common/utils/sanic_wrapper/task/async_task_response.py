from __future__ import annotations

import typing as t


class AsyncTaskResponse:
    __slots__ = (
        "_data",
        "_meta",
        "_status_code",
        "_headers",
    )

    def __init__(
        self,
        data: dict,
        status_code: int,
        *,
        headers: dict | None = None,
        meta: t.Any = None,
    ):
        self._data = data
        self._status_code = status_code
        self._meta = meta
        self._headers = headers

    @property
    def data(self) -> dict:
        return self._data

    @property
    def status(self) -> int:
        return self._status_code

    @property
    def meta(self) -> t.Any:
        return self._meta

    @property
    def headers(self) -> dict | None:
        return self._headers

    def to_dict(self) -> dict:
        result = {}
        result["data"] = self._data
        result["meta"] = self._meta
        result["headers"] = self._headers
        result["partial_complete"] = False  # ?
        result["is_success"] = True
        return result
