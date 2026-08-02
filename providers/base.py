import httpx


class ProviderError(Exception):
    pass


class RateLimited(ProviderError):
    pass


def est_tokens(s):
    return max(1, len(s) // 4)


class Provider:
    name = "base"
    tiers = {"micro": [], "smart": [], "deep": []}

    def __init__(self, cfg):
        self.cfg = cfg
        self.client = httpx.AsyncClient(timeout=90)

    def available(self):
        return False

    async def chat(self, messages, model, max_tokens=700, temperature=0.6):
        raise NotImplementedError

    async def close(self):
        await self.client.aclose()