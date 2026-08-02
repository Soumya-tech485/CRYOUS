CRYOUS PLUGIN BAY
=================
Drop any .py file here that defines:

    from agents.base import Agent

    class MyAgent(Agent):
        name = "weather"
        description = "..."
        keywords = ["weather", "temperature"]
        async def run(self, task, context=""):
            return self.done("summary spoken aloud", "full detail for the panel")

    AGENT = MyAgent

It is hot-loaded at startup. CRYOUS can also write its own plugins here —
just say:  "Cryous, create a plugin weather: fetch weather from open-meteo"