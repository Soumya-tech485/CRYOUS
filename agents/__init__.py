import importlib
import importlib.util
from types import SimpleNamespace

BUILTIN = ["system_agent", "file_agent", "research_agent", "browser_agent", "coder_agent",
           "data_agent", "report_agent", "email_agent", "reminder_agent", "memory_agent"]


class Registry:
    def __init__(self):
        self.agents = {}
        self.ctx = None

    def register(self, agent):
        self.agents[agent.name] = agent

    def get(self, name):
        return self.agents.get(name) if name else None

    def pick(self, task):
        best, bs = None, 0.999
        for a in self.agents.values():
            s = a.score(task)
            if s > bs:
                bs, best = s, a
        return best

    def describe(self):
        return " | ".join(f"{a.name} ({a.description})" for a in self.agents.values())


def build_registry(cfg, router, db, bus, brain):
    reg = Registry()
    ctx = SimpleNamespace(cfg=cfg, router=router, db=db, bus=bus, brain=brain, registry=reg)
    reg.ctx = ctx
    for mod in BUILTIN:
        try:
            m = importlib.import_module(f"agents.{mod}")
            reg.register(m.AGENT(ctx))
        except Exception as e:
            print(f"[agents] could not load {mod}: {e}")
    load_plugins(reg, ctx)
    return reg


def load_plugins(reg, ctx):
    pdir = ctx.cfg.root / "plugins"
    pdir.mkdir(exist_ok=True)
    for p in sorted(pdir.glob("*.py")):
        if p.name.startswith("_") or p.name == "README.txt":
            continue
        try:
            spec = importlib.util.spec_from_file_location(f"cryous_plugin_{p.stem}", p)
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
            if hasattr(m, "AGENT"):
                reg.register(m.AGENT(ctx))
                print(f"[plugins] loaded {p.name}")
        except Exception as e:
            print(f"[plugins] {p.name} failed: {e}")