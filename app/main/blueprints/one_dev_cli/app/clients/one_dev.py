from typing import Any, Dict, Optional, Union

from torpedo import CONFIG

from app.common.request_clients.http.base_http_client import BaseHTTPClient


class OneDevClient(BaseHTTPClient):
    """
    Class to handle all the inter service requests to OneDev service
    """

    def __init__(self):
        _one_dev_config: Dict[str, Union[str, int]] = CONFIG.config["ONE_DEV"]
        self._host: str = _one_dev_config["HOST"]
        super().__init__(timeout=_one_dev_config["TIMEOUT"])

    async def generate_code(self, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        path = "/end_user/v1/generate-code"
        result = await self.post(self._host + path, json=payload, headers=headers)
        return (await result.json()).get("data")

    async def generate_docs(self, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        path = "/end_user/v1/generate-docs"
        result = await self.post(url=self._host + path, json=payload, headers=headers)
        return (await result.json()).get("data")

    async def generate_test_cases(self, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        path = "/end_user/v1/generate-test-cases"
        result = await self.post(url=self._host + path, json=payload, headers=headers)
        return (await result.json()).get("data")

    async def generate_code_plan(self, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        path = "/end_user/v1/generate-code-plan"
        result = await self.post(url=self._host + path, json=payload, headers=headers)
        return (await result.json()).get("data")

    async def generate_diff(self, payload: Optional[Dict[str, Any]], headers: Dict[str, str]) -> Dict[str, Any]:
        path = "/end_user/v1/generate-diff"
        result = await self.post(url=self._host + path, json=payload, headers=headers)
        return (await result.json()).get("data")

    async def iterative_chat(self, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        path = "/end_user/v1/iterative-chat"
        result = await self.post(url=self._host + path, json=payload, headers=headers)
        return (await result.json()).get("data")

    async def plan_code_generation(self, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        path = "/end_user/v1/plan-code-generation"
        result = await self.post(url=self._host + path, json=payload, headers=headers)
        return (await result.json()).get("data")

    async def get_registered_repo_details(self, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        path = "/end_user/v1/get-registered-repo-details"
        result = await self.get(url=self._host + path, headers=headers, params=payload)
        return (await result.json()).get("data")

    async def get_job_status(self, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        path = "/end_user/v1/get-job-status"
        result = await self.get(url=self._host + path, headers=headers, params=payload)
        return (await result.json()).get("data")

    async def create_embedding(self, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        path = "/end_user/v1/create-embedding"
        result = await self.post(url=self._host + path, json=payload, headers=headers)
        return (await result.json()).get("data")

    async def verify_auth_token(self, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        path = "/end_user/v1/verify-auth-token"
        result = await self.post(url=self._host + path, json=payload, headers=headers)
        return (await result.json()).get("data")
