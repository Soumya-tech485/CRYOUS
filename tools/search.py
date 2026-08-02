import asyncio
from urllib.parse import quote

import httpx

try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS


async def web_search(q, n=6):
    """DuckDuckGo — free, no API key."""
    def _sync():
        with DDGS() as d:
            return list(d.text(q, max_results=n))
    try:
        return await asyncio.get_running_loop().run_in_executor(None, _sync)
    except Exception as e:
        print("[search]", e)
        return []


async def wiki_summary(q):
    """Wikipedia REST API — free, no key."""
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get("https://en.wikipedia.org/api/rest_v1/page/summary/" +
                            quote(q.title().replace(" ", "_")))
            if r.status_code == 200:
                return r.json().get("extract", "")
            r = await c.get("https://en.wikipedia.org/w/api.php",
                            params={"action": "query", "list": "search", "srsearch": q, "format": "json"})
            hits = r.json().get("query", {}).get("search", [])
            if hits:
                r2 = await c.get("https://en.wikipedia.org/api/rest_v1/page/summary/" + quote(hits[0]["title"]))
                if r2.status_code == 200:
                    return r2.json().get("extract", "")
    except Exception:
        pass
    return ""