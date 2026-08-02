import re
import webbrowser

import httpx

from .base import Agent


class BrowserAgent(Agent):
    name = "browser"
    description = "Open websites, Google/YouTube search, read and extract webpage content"
    keywords = ["open website", "go to", "youtube", "google", "browse", "visit", "url",
                "read the page", "extract from", "scrape", "website"]

    def score(self, task):
        s = super().score(task)
        if re.search(r"https?://|\.(com|org|net|io|ai)\b", task.lower()):
            s += 3
        return s

    async def run(self, task, context=""):
        t = task.lower()
        m = re.search(r"https?://\S+", task)
        url = m.group(0) if m else None

        if url and any(k in t for k in ("read", "extract", "summarize", "scrape")):
            return await self._read(url)
        if url:
            webbrowser.open(url)
            return self.done(f"Opening {url} in your browser, boss.")
        if "youtube" in t:
            q = t.replace("youtube", "").replace("play", "").strip()
            webbrowser.open(f"https://www.youtube.com/results?search_query={q.replace(' ', '+')}")
            return self.done(f"Searching YouTube for {q}.")
        if "google" in t or "go to" in t or "open" in t:
            q = re.sub(r"(google|search for|go to|open|website|the)", "", t).strip()
            if "." in q and " " not in q:
                webbrowser.open(f"https://{q}")
                return self.done(f"Opening {q}, boss.")
            webbrowser.open(f"https://www.google.com/search?q={q.replace(' ', '+')}")
            return self.done(f"Googling {q}, boss.")
        return self.done("Tell me which site to open, boss.")

    async def _read(self, url):
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as c:
            r = await c.get(url, headers={"User-Agent": "Mozilla/5.0"})
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        text = re.sub(r"\s+", " ", soup.get_text(" "))[:4000]
        try:
            out, _ = await self.ctx.router.ask(
                [{"role": "system", "content": "Summarize this webpage in under 80 words."},
                 {"role": "user", "content": text}], tier="micro", max_tokens=200)
            summ = out.strip()
        except Exception:
            summ = text[:200]
        return self.done(summ, text)


AGENT = BrowserAgent