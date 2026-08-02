class Agent:
    name = "base"
    description = ""
    keywords = []
    slow = False                      # slow agents run in the background, never blocking voice

    def __init__(self, ctx):
        self.ctx = ctx                # cfg, router, db, bus, brain, registry

    def score(self, task):
        t = task.lower()
        return sum(1 for k in self.keywords if k in t)

    async def run(self, task, context=""):
        return self.done("not implemented")

    @staticmethod
    def done(summary, detail="", artifacts=None):
        return {"summary": summary, "detail": detail, "artifacts": artifacts or []}