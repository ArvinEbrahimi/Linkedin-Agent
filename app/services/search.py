import asyncio
import json
import logging
import urllib.request

from app.config import Settings
from app.models.strategy import SearchResult

logger = logging.getLogger(__name__)


class SearchService:
    """Web search for trend and competitor research. Tavily first, DuckDuckGo fallback."""

    def __init__(self, settings: Settings) -> None:
        self._tavily_key = settings.tavily_api_key

    async def search(self, query: str, max_results: int = 5) -> tuple[list[SearchResult], str]:
        if self._tavily_key:
            try:
                results = await asyncio.to_thread(
                    self._tavily_search, query, max_results, self._tavily_key
                )
                if results:
                    return results, "tavily"
            except Exception:
                logger.exception("Tavily search failed for query=%r", query)

        try:
            results = await asyncio.to_thread(self._ddg_search, query, max_results)
            if results:
                return results, "duckduckgo"
        except Exception:
            logger.exception("DuckDuckGo search failed for query=%r", query)

        logger.warning("No search results for query=%r — continuing without web context", query)
        return [], "none"

    @staticmethod
    def _tavily_search(query: str, max_results: int, api_key: str) -> list[SearchResult]:
        payload = json.dumps(
            {
                "api_key": api_key,
                "query": query,
                "max_results": max_results,
                "search_depth": "basic",
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            "https://api.tavily.com/search",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        results: list[SearchResult] = []
        for item in data.get("results", [])[:max_results]:
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("content", item.get("snippet", ""))[:500],
                )
            )
        return results

    @staticmethod
    def _ddg_search(query: str, max_results: int) -> list[SearchResult]:
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            logger.warning("duckduckgo-search not installed — search fallback unavailable")
            return []

        results: list[SearchResult] = []
        with DDGS() as ddgs:
            for item in ddgs.text(query, max_results=max_results):
                results.append(
                    SearchResult(
                        title=item.get("title", ""),
                        url=item.get("href", item.get("link", "")),
                        snippet=item.get("body", item.get("snippet", ""))[:500],
                    )
                )
        return results

    @staticmethod
    def format_results_for_prompt(results: list[SearchResult]) -> str:
        if not results:
            return "No web search results available — rely on stored profile and general knowledge."
        lines = []
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. **{r.title}** ({r.url})\n   {r.snippet}")
        return "\n".join(lines)

    async def search_competitors(
        self, names: list[str], niche: str | None = None
    ) -> tuple[list[SearchResult], str]:
        niche_part = f" {niche}" if niche else ""
        all_results: list[SearchResult] = []
        provider = "none"

        for name in names[:5]:
            query = f"{name} LinkedIn personal brand content strategy{niche_part}"
            results, prov = await self.search(query, max_results=3)
            if prov != "none":
                provider = prov
            all_results.extend(results)

        return all_results[:12], provider
