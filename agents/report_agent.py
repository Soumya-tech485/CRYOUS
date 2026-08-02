import datetime

from .base import Agent
from tools.docs import write_docx, write_md, write_pdf


class ReportAgent(Agent):
    name = "report"
    description = "Generate reports, documents and notes as Markdown / DOCX / PDF"
    keywords = ["report", "pdf", "docx", "word document", "document", "presentation",
                "notes", "write a summary", "create a document", "letter"]
    slow = True

    async def run(self, task, context=""):
        t = task.lower()
        topic = task
        for w in ("create", "generate", "write", "make", "a", "an", "report", "pdf",
                  "docx", "document", "about", "on", "the", "me"):
            topic = topic.replace(f" {w} ", " ")
        topic = topic.strip(" .") or "Report"

        body = context if len(context) > 200 else None
        if not body:
            try:
                out, _ = await self.ctx.router.ask(
                    [{"role": "system", "content": "Write a structured report in markdown with ## sections. 350-500 words, factual tone."},
                     {"role": "user", "content": f"Topic: {topic}"}],
                    tier="smart", max_tokens=1200, use_cache=False)
                body = out
            except Exception as e:
                body = f"# {topic}\n\n(Content generation unavailable: {e})"

        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        base = self.ctx.cfg.out_dir / f"{stamp}_{topic[:24].replace(' ', '_')}"
        arts = []
        write_md(base.with_suffix(".md"), topic, body)
        arts.append(str(base.with_suffix(".md")))
        if "pdf" in t or "docx" not in t:
            write_pdf(base.with_suffix(".pdf"), topic, body)
            arts.append(str(base.with_suffix(".pdf")))
        if "docx" in t or "word" in t:
            write_docx(base.with_suffix(".docx"), topic, body)
            arts.append(str(base.with_suffix(".docx")))
        return self.done(f"Report on '{topic}' is ready, boss — {len(arts)} files in data/output.",
                         body[:1500], arts)


AGENT = ReportAgent