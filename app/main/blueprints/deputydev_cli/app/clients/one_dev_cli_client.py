from deputydev_core.clients.http.service_clients.one_dev_client import OneDevClient
from typing import Any, Dict, Optional


class OneDevCliClient(OneDevClient):
    async def generate_code(
            self, payload: Dict[str, Any], headers: Dict[str, str]
    ) -> Dict[str, Any]:
        path = "/end_user/v1/generate-code"
        result = await self.post(self._host + path, json=payload, headers=headers)
        return (await result.json()).get("data")

    async def generate_docs(
            self, payload: Dict[str, Any], headers: Dict[str, str]
    ) -> Dict[str, Any]:
        path = "/end_user/v1/generate-docs"
        result = await self.post(url=self._host + path, json=payload, headers=headers)
        return (await result.json()).get("data")

    async def generate_test_cases(
            self, payload: Dict[str, Any], headers: Dict[str, str]
    ) -> Dict[str, Any]:
        path = "/end_user/v1/generate-test-cases"
        result = await self.post(url=self._host + path, json=payload, headers=headers)
        return (await result.json()).get("data")

    async def generate_code_plan(
            self, payload: Dict[str, Any], headers: Dict[str, str]
    ) -> Dict[str, Any]:
        path = "/end_user/v1/generate-code-plan"
        result = await self.post(url=self._host + path, json=payload, headers=headers)
        return (await result.json()).get("data")

    async def generate_diff(
            self, payload: Optional[Dict[str, Any]], headers: Dict[str, str]
    ) -> Dict[str, Any]:
        path = "/end_user/v1/generate-diff"
        result = await self.post(url=self._host + path, json=payload, headers=headers)
        return (await result.json()).get("data")

    async def iterative_chat(
            self, payload: Dict[str, Any], headers: Dict[str, str]
    ) -> Dict[str, Any]:
        path = "/end_user/v1/iterative-chat"
        result = await self.post(url=self._host + path, json=payload, headers=headers)
        return (await result.json()).get("data")

    async def record_feedback(
            self, payload: Dict[str, Any], headers: Dict[str, str]
    ) -> Dict[str, Any]:
        path = "/end_user/v1/record-feedback"
        result = await self.post(url=self._host + path, json=payload, headers=headers)
        return (await result.json()).get("data")

    async def plan_to_code(
            self, payload: Dict[str, Any], headers: Dict[str, str]
    ) -> Dict[str, Any]:
        path = "/end_user/v1/plan-code-generation"
        result = await self.post(url=self._host + path, json=payload, headers=headers)
        return (await result.json()).get("data")

    async def get_registered_repo_details(
            self, payload: Dict[str, Any], headers: Dict[str, str]
    ) -> Dict[str, Any]:
        path = "/end_user/v1/get-registered-repo-details"
        result = await self.get(url=self._host + path, headers=headers, params=payload)
        return (await result.json()).get("data")

    async def get_job_status(
            self, payload: Dict[str, Any], headers: Dict[str, str]
    ) -> Dict[str, Any]:
        path = "/end_user/v1/get-job-status"
        result = await self.get(url=self._host + path, headers=headers, params=payload)
        return (await result.json()).get("data")

    async def create_embedding(
            self, payload: Dict[str, Any], headers: Dict[str, str]
    ) -> Dict[str, Any]:
        path = "/end_user/v1/create-embedding"
        result = await self.post(url=self._host + path, json=payload, headers=headers)
        return (await result.json()).get("data")

    async def verify_auth_token(self, headers: Dict[str, str]) -> Dict[str, Any]:
        """
        Verify the authentication token for the user.

        Args:
            headers (Dict[str, str]): The headers containing the authentication token.

        Returns:
            Dict[str, Any]: A dictionary containing the verification result if successful, otherwise None.

        Raises:
            Exception: Raises an exception if the request fails or the response is not valid.
        """
        path = "/end_user/v1/verify-auth-token"
        result = await self.post(url=self._host + path, headers=headers)
        return (await result.json()).get("data")

    async def get_session(self, headers: Dict[str, str]) -> Dict[str, Any]:
        """
        Retrieve the session information for the user.

        Args:
            headers (Dict[str, str]): The headers containing authentication information.

        Returns:
            Dict[str, Any]: A dictionary containing the session data if successful, otherwise None.

        Raises:
            Exception: Raises an exception if the request fails or the response is not valid.
        """
        path = "/end_user/v1/get-session"
        result = await self.get(url=self._host + path, headers=headers)
        return (await result.json()).get("data")

    async def get_essential_configs(
            self, headers: Dict[str, str]
    ) -> Optional[Dict[str, Any]]:
        path = "/end_user/v1/get-essential-configs"
        result = await self.get(url=self._host + path, headers=headers)
        return (await result.json()).get("data")

    async def get_configs(self, headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
        path = "/end_user/v1/get-configs"
        result = await self.get(url=self._host + path, headers=headers)
        return (await result.json()).get("data")

    async def fetch_relevant_chat_history(
            self, payload: Dict[str, Any], headers: Dict[str, str]
    ) -> Dict[str, Any]:
        path = "/end_user/v1/relevant-chat-history"
        result = await self.post(url=self._host + path, json=payload, headers=headers)
        return (await result.json()).get("data")
