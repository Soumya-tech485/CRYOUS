from .base import Provider, ProviderError, RateLimited, est_tokens


class GeminiProvider(Provider):
    name = "gemini"
    tiers = {
        "micro": ["gemini-2.5-flash-lite"],
        "smart": ["gemini-2.5-flash"],
        "deep":  ["gemini-2.5-flash"],
    }

    def __init__(self, cfg):
        super().__init__(cfg)
        self.key = cfg.gemini_key

    def available(self):
        return bool(self.key)

    async def chat(self, messages, model, max_tokens=700, temperature=0.6):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        contents, system = [], None
        for m in messages:
            if m["role"] == "system":
                system = (system or "") + m["content"] + "\n"
            else:
                contents.append({"role": "user" if m["role"] == "user" else "model",
                                 "parts": [{"text": m["content"]}]})
        body = {"contents": contents,
                "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens}}
        if system:
            body["systemInstruction"] = {"parts": [{"text": system.strip()}]}

        r = await self.client.post(url, params={"key": self.key}, json=body)
        if r.status_code == 429:
            raise RateLimited("gemini 429")
        if r.status_code >= 400:
            raise ProviderError(f"gemini {r.status_code}: {r.text[:200]}")
        d = r.json()
        try:
            text = "".join(p.get("text", "") for p in d["candidates"][0]["content"]["parts"])
        except (KeyError, IndexError):
            raise ProviderError("gemini: blocked or empty response")
        u = d.get("usageMetadata", {})
        return text, u.get("promptTokenCount", est_tokens(str(body))), u.get("candidatesTokenCount", est_tokens(text))