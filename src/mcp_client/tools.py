"""LangChain-compatible wrappers around tools served by FastMCP over SSE."""

import asyncio
import json
import threading
from typing import Any, Coroutine

from fastmcp import Client

from src.utils.config import MCPSettings, get_config


class MCPToolError(RuntimeError):
    """Raised when a remote MCP tool cannot be called successfully."""


async def _call_tool(name: str, arguments: dict[str, Any], settings: MCPSettings) -> dict[str, Any]:
    """Call one MCP tool and decode its JSON text response."""
    last_error: Exception | None = None
    for attempt in range(settings.max_retries + 1):
        try:
            async with Client(settings.url, timeout=settings.connect_timeout_seconds) as client:
                content = await client.call_tool(
                    name,
                    arguments,
                    timeout=settings.tool_timeout_seconds,
                )
            text = "".join(item.text for item in content if hasattr(item, "text"))
            if not text:
                raise MCPToolError(f"MCP tool '{name}' returned no text content")
            payload = json.loads(text)
            if not isinstance(payload, dict):
                raise MCPToolError(f"MCP tool '{name}' returned a non-object JSON response")
            return payload
        except (json.JSONDecodeError, MCPToolError) as exc:
            # A malformed tool response will not become valid on retry.
            raise MCPToolError(f"MCP tool '{name}' returned an invalid response: {exc}") from exc
        except Exception as exc:
            last_error = exc
            if attempt < settings.max_retries:
                await asyncio.sleep(0.2 * (attempt + 1))
    raise MCPToolError(
        f"MCP tool '{name}' failed after {settings.max_retries + 1} attempt(s): {last_error}"
    ) from last_error


def _run_sync(coroutine: Coroutine[Any, Any, dict[str, Any]]) -> dict[str, Any]:
    """Run an async MCP request safely from synchronous LangChain tool execution."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coroutine)

    # FastAPI's async routes can invoke the synchronous agent runner. A separate
    # thread avoids nesting an event loop in that situation.
    result: dict[str, Any] = {}
    error: list[BaseException] = []

    def runner() -> None:
        try:
            result.update(asyncio.run(coroutine))
        except BaseException as exc:  # re-raised in the calling thread below
            error.append(exc)

    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    thread.join()
    if error:
        raise error[0]
    return result


def search_tool(query: str) -> dict[str, Any]:
    """Search through the configured remote MCP server rather than local Python."""
    if not query or not query.strip():
        return {"sources": [], "information": [], "status": "error", "error": "Query is required"}
    settings = get_config().mcp
    return _run_sync(_call_tool("search_tool", {"query": query}, settings))


search_tool.__name__ = "search_tool"
search_tool.__doc__ = "Search the web through the configured MarketScout MCP server."
