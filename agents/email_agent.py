import asyncio
import datetime
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from .base import Agent


class EmailAgent(Agent):
    name = "email"
    description = "Draft and send emails via SMTP, professional letters"
    keywords = ["email", "mail", "send a message", "draft", "letter to"]

    async def run(self, task, context=""):
        to = re.search(r"to\s+([\w.+-]+@[\w-]+\.[\w.]+)", task)
        subj = re.search(r"(?:subject|about|titled)\s+[:\"']?([^,\"\']+)", task.lower())
        subject = subj.group(1).strip() if subj else task[:60]

        body = context if len(context) > 120 else None
        if not body:
            try:
                out, _ = await self.ctx.router.ask(
                    [{"role": "system", "content": "Write a concise professional email body. No subject line, no markdown."},
                     {"role": "user", "content": task}], tier="micro", max_tokens=300, use_cache=False)
                body = out
            except Exception:
                body = task

        if to and self.ctx.cfg.smtp_host:
            await asyncio.get_running_loop().run_in_executor(
                None, self._send, to.group(1), subject, body)
            return self.done(f"Email sent to {to.group(1)}, boss.", body)

        p = self.ctx.cfg.out_dir / f"email_{datetime.datetime.now():%H%M%S}.md"
        p.write_text(f"TO: {to.group(1) if to else '(add recipient)'}\nSUBJECT: {subject}\n\n{body}",
                     encoding="utf-8")
        note = "draft saved" + ("" if to else " — add SMTP credentials in .env to send directly")
        return self.done(f"Email {note}, boss.", body, [str(p)])

    def _send(self, to, subject, body):
        c = self.ctx.cfg
        msg = MIMEMultipart()
        msg["From"], msg["To"], msg["Subject"] = c.smtp_user, to, subject
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP(c.smtp_host, c.smtp_port) as s:
            s.starttls()
            s.login(c.smtp_user, c.smtp_pass)
            s.sendmail(c.smtp_user, to, msg.as_string())


AGENT = EmailAgent