"""Small request-boundary safeguards for JSON-only API routes."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any


class JsonRequestSizeLimitMiddleware:
    """Bound JSON request bodies without buffering multipart image uploads."""

    def __init__(self, app: Callable[..., Any], max_bytes: int = 1024 * 1024) -> None:
        if max_bytes <= 0:
            raise ValueError("max_bytes must be positive")
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: dict[str, Any], receive: Callable[..., Any], send: Callable[..., Any]) -> None:
        if scope["type"] != "http" or scope.get("method") != "POST" or scope.get("path") not in {
            "/predictions",
            "/recommendations/current",
        }:
            await self.app(scope, receive, send)
            return

        headers = {key.lower(): value for key, value in scope.get("headers", [])}
        content_type = headers.get(b"content-type", b"").split(b";", 1)[0].strip().lower()
        if content_type != b"application/json":
            await self.app(scope, receive, send)
            return

        try:
            content_length = int(headers.get(b"content-length", b"0"))
        except ValueError:
            content_length = 0
        if content_length > self.max_bytes:
            await self._reject(send)
            return

        messages: list[dict[str, Any]] = []
        total_bytes = 0
        while True:
            message = await receive()
            messages.append(message)
            if message["type"] != "http.request":
                break
            total_bytes += len(message.get("body", b""))
            if total_bytes > self.max_bytes:
                await self._reject(send)
                return
            if not message.get("more_body", False):
                break

        message_index = 0

        async def replay_receive() -> dict[str, Any]:
            nonlocal message_index
            if message_index < len(messages):
                message = messages[message_index]
                message_index += 1
                return message
            return await receive()

        await self.app(scope, replay_receive, send)

    async def _reject(self, send: Callable[..., Any]) -> None:
        body = b'{"detail":{"code":"request_too_large","message":"JSON request exceeds the 1 MiB API limit."}}'
        await send({
            "type": "http.response.start",
            "status": 413,
            "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode("ascii"))],
        })
        await send({"type": "http.response.body", "body": body})
