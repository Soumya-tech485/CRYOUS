from .base import Provider, ProviderError, RateLimited, est_tokens

# Free models rotate — refresh the list at https://openrouter.ai/models?price=0
class OpenRouterProvider(Provider):
    name = "openrouter"
    tiers = {
        "micro": ["meta-llama/llama-3.1-8b-instruct:free"],
        "smart": ["meta-llama/llama-3.3-70b-instruct:free"],
        "deep":  ["meta-llama/llama-3.3-70b-instruct:free"],
    }

    def available(self):
        return bool(self.cfg.openrouter_key)

    async def chat(self, messages, model, max_tokens=700, temperature=0.6):
        r = await self.client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.cfg.openrouter_key}",
                     "HTTP-Referer": "http://localhost", "X-Title": "CRYOUS"},
            json={"model": model, "messages": messages, "temperature": temperature,
                  "max_tokens": max_tokens})
        if r.status_code == 429:
            raise RateLimited("openrouter 429")
        if r.status_code >= 400:
            raise ProviderError(f"openrouter {r.status_code}: {r.text[:200]}")
        d = r.json()
        text = d["choices"][0]["message"]["content"]
        u = d.get("usage", {})
        return text, u.get("prompt_tokens", est_tokens(str(messages))), u.get("completion_tokens", est_tokens(text))