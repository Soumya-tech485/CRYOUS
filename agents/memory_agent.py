import re

from .base import Agent


class MemoryAgent(Agent):
    name = "memory"
    description = "Remember facts, recall what CRYOUS knows, forget on command"
    keywords = ["remember", "recall", "what do you know", "forget", "my name", "what did i"]

    async def run(self, task, context=""):
        t = task.lower()
        if "forget" in t:
            m = re.search(r"forget (?:about )?(.+)", t)
            if m:
                self.ctx.db.forget(m.group(1).strip())
            return self.done("Forgotten, boss.")
        if "remember" in t:
            m = re.search(r"remember (?:that )?(.+)", t)
            if m:
                fact = m.group(1)
                self.ctx.db.set_fact("note:" + fact[:32], fact)
                return self.done(f"Committed to memory, boss: {fact}")
        if "what do you know" in t or "recall" in t or "what did i" in t:
            facts = self.ctx.db.facts(15)
            if not facts:
                return self.done("My memory of your preferences is empty so far, boss.")
            return self.done(f"I remember {len(facts)} things, boss.",
                             "\n".join("• " + f for f in facts))
        return self.done("Ask me to remember, recall, or forget something, boss.")


AGENT = MemoryAgent