from .base import Provider, ProviderError, est_tokens


class OllamaProvider(Provider):
    """Optional local models — zero tokens, uses your G15's GPU. Set OLLAMA_URL in .env."""
    name = "ollama"
    tiers = {
        "micro": ["llama3.2:1b"],
        "smart": ["llama3.1:8b"],
        "deep":  ["llama3.1:8b"],
    }

    def available(self):
        return bool(self.cfg.ollama_url)

    async def chat(self, messages, model, max_tokens=700, temperature=0.6):
        r = await self.client.post(
            f"{self.cfg.ollama_url}/api/chat",
            json={"model": model, "messages": messages, "stream": False,
                  "options": {"temperature": temperature, "num_predict": max_tokens}})
        if r.status_code >= 400:
            raise ProviderError(f"ollama {r.status_code}")
        text = r.json()["message"]["content"]
        return text, est_tokens(str(messages)), est_tokens(text)