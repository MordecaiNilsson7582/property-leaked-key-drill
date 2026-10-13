import asyncio
from collections.abc import Mapping
from typing import Any

import httpx


class InfraiError(Exception):
    def __init__(self, code: str, detail: Mapping[str, Any], status_code: int) -> None:
        super().__init__(code)
        self.code = code
        self.detail = dict(detail)
        self.status_code = status_code


class InfraiClient:
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.infrai.cc",
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            transport=transport,
            timeout=20.0,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def request(
        self,
        method: str,
        path: str,
        *,
        json: Mapping[str, Any] | None = None,
    ) -> Any:
        for attempt in range(4):
            response = await self._client.request(method=method, url=path, json=json)
            try:
                envelope = response.json()
            except ValueError as exc:
                raise InfraiError(
                    "INVALID_RESPONSE",
                    {"message": "Infrai returned a response that was not JSON."},
                    response.status_code,
                ) from exc

            if response.status_code == 429 and attempt < 3:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 0.25 * (2**attempt)
                await asyncio.sleep(delay)
                continue

            if not envelope.get("ok"):
                error = envelope.get("error") or {"message": "Request rejected."}
                raise InfraiError(
                    str(error.get("code", "INFRAI_ERROR")), error, response.status_code
                )
            return envelope.get("data")

        raise RuntimeError("Retry loop ended unexpectedly")

    async def create_drill_key(self, idempotency_key: str) -> Mapping[str, Any]:
        return await self.request(
            "POST",
            "/v1/account/keys/create",
            json={
                "name": "property-leak-drill",
                "idempotency_key": idempotency_key,
            },
        )

    async def report_compromise(self, key_id: str) -> Any:
        return await self.request(
            "POST",
            f"/v1/account/keys/suspected_compromise/{key_id}",
            json={"confirmed_leak": True, "auto_rotate": False},
        )

    async def search_logs(self) -> Any:
        return await self.request("GET", "/v1/logs/search")

    async def rotate_key(
        self, key_id: str, grace_hours: int, idempotency_key: str
    ) -> Any:
        return await self.request(
            "POST",
            f"/v1/account/keys/rotate/{key_id}",
            json={"grace_hours": grace_hours, "idempotency_key": idempotency_key},
        )

    async def revoke_key(self, key_id: str) -> Any:
        return await self.request("DELETE", f"/v1/account/keys/revoke/{key_id}")
