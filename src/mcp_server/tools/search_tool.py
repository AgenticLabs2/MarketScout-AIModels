"""Dependency-light web search tool exposed through FastMCP and LangChain."""

from html import unescape
import re
from urllib.parse import parse_qs, unquote, urlparse

import requests
import trafilatura


_RESULT_RE = re.compile(
    r'<a[^>]+class="[^"]*result__a[^"]*"[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
_TAG_RE = re.compile(r"<[^>]+>")


def _result_url(raw_url: str) -> str:
    url = unescape(raw_url)
    parsed = urlparse(url)
    redirected = parse_qs(parsed.query).get("uddg")
    return unquote(redirected[0]) if redirected else url


def search_tool(query: str) -> dict:
    """Search DuckDuckGo and return up to five sources with extracted text."""
    if not query or not query.strip():
        return {"sources": [], "information": [], "status": "error", "error": "Query is required"}

    try:
        response = requests.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers={"User-Agent": "Mozilla/5.0 (compatible; MarketScout/0.1)"},
            timeout=10,
        )
        response.raise_for_status()
        matches = _RESULT_RE.findall(response.text)[:5]
        sources: list[str] = []
        information: list[str] = []

        for raw_url, raw_title in matches:
            url = _result_url(raw_url)
            title = unescape(_TAG_RE.sub("", raw_title)).strip()
            extracted = None
            try:
                downloaded = trafilatura.fetch_url(url)
                if downloaded:
                    extracted = trafilatura.extract(downloaded, include_links=False)
            except Exception:
                extracted = None
            sources.append(url)
            information.append((extracted or title)[:8000])

        return {"sources": sources, "information": information, "status": "success"}
    except Exception as exc:
        return {"sources": [], "information": [], "status": "error", "error": str(exc)}


search_tool.__name__ = "search_tool"
search_tool.__doc__ = "Search the web and return source URLs with extracted information."
