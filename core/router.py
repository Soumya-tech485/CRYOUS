import datetime
import hashlib
import time

from providers.base import ProviderError, RateLimited
from providers.gemini import GeminiProvider
from providers.groq import GroqProvider
from providers.openrouter import OpenRouterProvider
from providers.ollama import OllamaProvider

DEEP_HINTS = ("research", "analyze", "compare", "report", "debug", "refactor",
              "architecture", "business plan", "paper", "presentation", "explain code")


class OmniRouter:
    """Token-efficient multi-provider router.

    Efficiency stack:
      1. task tiering   — small talk -> tiny models, hard work -> big models
      2. exact cache    — repeated questions cost 0 tokens
      3. compression    — old history is squeezed before sending
      4. weekly budget  — hard cap across all providers (default 1.5B)
      5. failover       — latency/success-weighted, with 429 cooldowns
    """

    def __init__(self, cfg, db):
        self.cfg, self.db = cfg, db
        self.providers = [p for p in (GeminiProvider(cfg), GroqProvider(cfg),
                                      OpenRouterProvider(cfg), OllamaProvider(cfg)) if p.available()]
        self.cooldown = {}
        self.cache_hits = 0

    def classify(self, text):
        t = text.lower()
        words = len(t.split())
        if any(h in t for h in DEEP_HINTS) or words > 45:
            return "deep"
        if words > 12:
            return "smart"
        return "micro"

    def _order(self, tier):
        scores = self.db.provider_scores()
        now = time.time()
        out = []
        for p in self.providers:
            if self.cooldown.get(p.name, 0) > now:
                continue
            lat, suc = scores.get(p.name, (0.6, 1.0))
            score = suc / (0.25 + lat)
            for model in p.tiers.get(tier, []):
                out.append((score, p, model))
        out.sort(key=lambda x: -x[0])
        return [(p, m) for _, p, m in out]

    def compress(self, messages):
        sysm = [m for m in messages if m["role"] == "system"]
        rest = [m for m in messages if m["role"] != "system"]
        keep, old = rest[-self.cfg.max_history:], rest[:-self.cfg.max_history]
        out = list(sysm)
        if old:
            gist = " | ".join(f'{m["role"]}: {m["content"][:90]}' for m in old[-4:])
            out.append({"role": "system", "content": "Compressed earlier context: " + gist})
        out += keep
        total = sum(len(m["content"]) for m in out)
        while total > 12000 and len(out) > 2:          # hard cap ~3k tokens
            out.pop(1)
            total = sum(len(m["content"]) for m in out)
        return out

    def cache_key(self, messages, tier):
        last_user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        return hashlib.sha256(f"{tier}:{last_user.strip().lower()}".encode()).hexdigest()

    async def ask(self, messages, tier=None, max_tokens=700, temperature=0.6, use_cache=True):
        if not self.budget_ok():
            raise ProviderError("Weekly token budget exhausted — resets Monday. Raise WEEKLY_TOKEN_BUDGET or add keys.")
        tier = tier or self.classify(messages[-1]["content"] if messages else "")
        key = self.cache_key(messages, tier) if use_cache else None
        if key:
            hit = self.db.cache_get(key)
            if hit is not None:
                self.cache_hits += 1
                return hit, {"provider": "cache", "model": "cache", "tokens": 0, "tier": tier}

        msgs = self.compress(messages)
        last_err = ProviderError("no providers configured — add a free API key to .env")
        for prov, model in self._order(tier):
            try:
                t0 = time.time()
                text, pt, ct = await prov.chat(msgs, model, max_tokens, temperature)
                self.db.log_usage(prov.name, tier, pt, ct)
                self.db.provider_feedback(prov.name, time.time() - t0, True)
                if key and temperature <= 0.8 and text.strip():
                    self.db.cache_set(key, text)
                return text, {"provider": prov.name, "model": model, "tokens": pt + ct, "tier": tier}
            except RateLimited as e:
                self.cooldown[prov.name] = time.time() + 120
                last_err = e
            except Exception as e:
                self.db.provider_feedback(prov.name, 1.5, False)
                last_err = e
        raise ProviderError(f"all providers failed ({last_err})")

    def week_start(self):
        now = datetime.datetime.now()
        return (now - datetime.timedelta(days=now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0).timestamp()

    def budget_ok(self):
        return self.db.tokens_since(self.week_start()) < self.cfg.weekly_budget

    def usage(self):
        used = self.db.tokens_since(self.week_start())
        return {"used": used, "budget": self.cfg.weekly_budget,
                "pct": round(100 * used / max(1, self.cfg.weekly_budget), 4),
                "cache_hits": self.cache_hits}