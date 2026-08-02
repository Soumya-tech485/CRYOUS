import datetime
import re

from .base import Agent
from tools.search import web_search, wiki_summary

STOP = ["research", "find out", "look up", "search for", "search", "tell me about",
        "what is", "who is", "give me", "latest", "news about", "information about", "the", "about"]


class ResearchAgent(Agent):
    name = "research"
    description = "Multi-source web research with citations and spoken summaries"
    keywords = ["research", "find out", "look up", "who is", "what is", "tell me about",
                "news", "search for", "facts", "price", "compare", "wikipedia"]
    slow = True

    async def run(self, task, context=""):
        q = self._clean(task)
        hits = await web_search(q, 6)
        wiki = await wiki_summary(q)

        lines = []
        if wiki:
            lines.append(f"[Wikipedia]\n{wiki}\n")
        for i, h in enumerate(hits, 1):
            lines.append(f"[{i}] {h.get('title', '')}\n{h.get('body', '')[:220]}\n{h.get('href', '')}")
        detail = "\n\n".join(lines) or "No results found, boss."
        summary = await self._verbal(detail)

        p = self.ctx.cfg.out_dir / f"research_{datetime.datetime.now():%Y%m%d_%H%M%S}.md"
        p.write_text(f"# Research: {q}\n\n{detail}\n", encoding="utf-8")
        return self.done(summary, detail, [str(p)])

    def _clean(self, task):
        t = task.lower()
        for s in sorted(STOP, key=len, reverse=True):
            t = t.replace(s, " ")
        return re.sub(r"\s+", " ", t).strip() or task

    async def _verbal(self, detail):
        try:
            out, _ = await self.ctx.router.ask(
                [{"role": "system", "content": "Summarize this research for speech in max 45 words. No citations, no markdown."},
                 {"role": "user", "content": detail[:3500]}],
                tier="micro", max_tokens=120)
            return out.strip()
        except Exception:
            return detail[:220]


AGENT = ResearchAgent