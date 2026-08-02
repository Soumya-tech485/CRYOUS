import re


class Improver:
    """Lets CRYOUS grow: learned skills (zero-token shortcuts) + self-written plugins."""

    def __init__(self, cfg, db):
        self.cfg, self.db = cfg, db

    def learn_command(self, trigger, action):
        self.db.add_skill(trigger, action)

    def parse_learn(self, text):
        m = re.search(r"learn(?: this)?(?: command)?[: ]+when i say [\"']?(.+?)[\"']?[,.]+ ?(?:do|then|say|run)? ?(.+)$",
                      text.lower())
        if m:
            return m.group(1).strip(), m.group(2).strip()
        return None

    async def write_plugin(self, router, name, spec):
        prompt = [
            {"role": "system",
             "content": "Write a CRYOUS plugin: a single Python file defining class AGENT(Agent) with attributes "
                        "name, description, keywords (list) and async def run(self, task, context='') returning "
                        "{'summary': str, 'detail': str}. Import Agent from agents.base. Code only, no markdown."},
            {"role": "user", "content": f"Plugin '{name}': {spec}"},
        ]
        code, _ = await router.ask(prompt, tier="smart", max_tokens=900, use_cache=False)
        code = re.sub(r"^```(?:python)?|```$", "", code.strip(), flags=re.M).strip()
        compile(code, f"plugin_{name}.py", "exec")          # safety gate: must be valid Python
        p = self.cfg.root / "plugins" / f"{name}.py"
        p.write_text(code, encoding="utf-8")
        self.db.audit("plugin", f"self-written plugin installed: {name}")
        return p