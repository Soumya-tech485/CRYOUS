import asyncio
import datetime
import re
import subprocess
import sys

from .base import Agent


class CoderAgent(Agent):
    name = "coder"
    description = "Write, run, debug and explain code in a sandboxed Python environment"
    keywords = ["code", "script", "python", "program", "function", "debug", "fix this code",
                "run this", "write a function", "refactor", "explain this code", "bug"]

    async def run(self, task, context=""):
        t = task.lower()
        code = self._extract_code(context) or self._extract_code(task)
        if ("run" in t or "execute" in t) and code:
            return await self._run_code(code)
        if code and any(k in t for k in ("debug", "fix", "error", "bug", "wrong")):
            return await self._ask("Find the bug and give the corrected code plus a 2-line explanation.", code, "Debug report")
        if "explain" in t and code:
            return await self._ask("Explain this code briefly in bullet points.", code, "Explanation")
        return await self._write(task)

    def _extract_code(self, text):
        m = re.search(r"```(?:python)?\n?(.*?)```", text, re.S)
        if m:
            return m.group(1).strip()
        lines = [l for l in text.splitlines()
                 if l.startswith(("def ", "import ", "from ", "print(", "for ", "class "))]
        return "\n".join(lines) if len(lines) >= 2 else None

    async def _run_code(self, code):
        p = self.ctx.cfg.out_dir / f"run_{datetime.datetime.now():%H%M%S}.py"
        p.write_text(code, encoding="utf-8")

        def _exec():
            try:
                r = subprocess.run([sys.executable, str(p)], capture_output=True, text=True,
                                   timeout=20, cwd=str(self.ctx.cfg.out_dir))
                return r.stdout[-2000:], r.stderr[-1000:], r.returncode
            except subprocess.TimeoutExpired:
                return "", "timed out after 20s", -1

        out, err, rc = await asyncio.get_running_loop().run_in_executor(None, _exec)
        self.ctx.db.audit("exec", str(p))
        summ = "Ran your code, boss — clean run." if rc == 0 and not err else f"Finished with exit code {rc}."
        return self.done(summ, f"STDOUT:\n{out}\nSTDERR:\n{err}", [str(p)])

    async def _ask(self, instruction, code, label):
        out, _ = await self.ctx.router.ask(
            [{"role": "system", "content": "You are a senior engineer. Be precise and brief."},
             {"role": "user", "content": instruction + "\n\n" + code}], tier="smart", max_tokens=700)
        return self.done(f"{label} ready, boss.", out)

    async def _write(self, task):
        out, _ = await self.ctx.router.ask(
            [{"role": "system", "content": "Write clean, efficient Python. Reply with a single ```python code block and 2 sentences of notes."},
             {"role": "user", "content": task}], tier="smart", max_tokens=900, use_cache=False)
        code = self._extract_code(out) or out
        p = self.ctx.cfg.out_dir / f"gen_{datetime.datetime.now():%H%M%S}.py"
        p.write_text(code, encoding="utf-8")
        return self.done("Code written and saved, boss.", out, [str(p)])


AGENT = CoderAgent