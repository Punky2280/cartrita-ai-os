import time
from datetime import datetime, timedelta
from typing import Any, Dict

from .base_tool import AdvancedCartritaTool, ToolCategory, ToolMetrics


class WebSearchTool(AdvancedCartritaTool):
    name: str = "web_search"
    description: str = "Search the web for information"
    category: ToolCategory = ToolCategory.WEB_SEARCH
    cost_factor: float = 2.0
    rate_limit: int = 10

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not hasattr(self, "_metrics"):
            self._metrics = ToolMetrics(name=self.name)
        self._search_cache: Dict[str, Any] = {}
        self._cache_expiry: Dict[str, datetime] = {}

    def do_execute(self, *args, **kwargs) -> str:
        def parse_args():
            if args:
                return str(args[0]), (
                    int(args[1]) if len(args) > 1 else int(kwargs.get("num_results", 5))
                )
            return str(kwargs.get("query")), int(kwargs.get("num_results", 5))

        query, num_results = parse_args()
        if not query:
            return "query is required"

        cache_key = f"{query}:{num_results}"
        if (
            cache_key in self._search_cache
            and cache_key in self._cache_expiry
            and self._cache_expiry[cache_key] > datetime.utcnow()
        ):
            self._record_cache_hit()
            return self._search_cache[cache_key]

        results = [
            {
                "title": f"Search result {i + 1} for '{query}'",
                "url": f"https://example.com/result-{i + 1}",
                "snippet": f"This is a relevant snippet about {query} from result {i + 1}",
            }
            for i in range(min(num_results, 5))
        ]

        formatted = [
            f"{i}. {r['title']}\n   {r['snippet']}\n   URL: {r['url']}"
            for i, r in enumerate(results, 1)
        ]
        text = "\n\n".join(formatted)
        self._search_cache[cache_key] = text
        self._cache_expiry[cache_key] = datetime.utcnow() + timedelta(hours=1)
        return text

    def _record_cache_hit(self) -> None:
        start = time.time()
        self._last_call_time = start
        if not hasattr(self, "_call_history") or self._call_history is None:
            self._call_history = []
        self._call_history.append(start)
        cutoff = start - 3600
        # filter in-place to avoid reassign lint warning
        filtered = [t for t in self._call_history if t > cutoff]
        self._call_history.clear()
        self._call_history.extend(filtered)
        self._update_metrics(True, 0.0)
