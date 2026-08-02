from .base import Provider, ProviderError, RateLimited, est_tokens


class GroqProvider(Provider):
    name = "groq"
    tiers = {
        "micro": ["llama-3.1-8b-instant"],
        "smart": ["llama-3.3-70b-versatile"],
        "deep":  ["llama-3.3-70b-versatile"],
    }

    def available(self):
        return bool(self.cfg.groq_key)

    async def chat(self, messages, model, max_tokens=700, temperature=0.6):
        r = await self.client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.cfg.groq_key}"},
            json={"model": model, "messages": messages, "temperature": temperature,
                  "max_completion_tokens": max_tokens})
        if r.status_code == 429:
            raise RateLimited("groq 429")
        if r.status_code >= 400:
            raise ProviderError(f"groq {r.status_code}: {r.text[:200]}")
        d = r.json()
        text = d["choices"][0]["message"]["content"]
        u = d.get("usage", {})
        return text, u.get("prompt_tokens", est_tokens(str(messages))), u.get("completion_tokens", est_tokens(text))