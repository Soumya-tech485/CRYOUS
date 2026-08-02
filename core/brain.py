import asyncio
import datetime
import json
import re
import traceback
import webbrowser

SYS = ("You are CRYOUS, a Jarvis-class personal AI operating system running locally on the boss's Dell G15. "
       "Address the user as 'boss'. Be concise, competent, lightly witty. Keep replies under 120 words unless detail is requested. "
       "Date: {date}. Known user preferences: {facts}\n"
       "If the request needs a real-world action, respond with ONLY this JSON (no markdown): "
       '{{"reply":"<spoken summary, max 25 words>","action":{{"agent":"<one of: {names}>","task":"<precise task>"}}}}\n'
       "For multi-step requests use {{\"reply\":\"...\",\"plan\":[{{\"agent\":\"..\",\"task\":\"..\"}}, ...]}}.\n"
       "Available agents -> {agents}\n"
       "For plain conversation, reply with normal text only (never JSON).")


class Brain:
    def __init__(self, cfg, router, db, improver):
        self.cfg, self.router, self.db, self.improver = cfg, router, db, improver
        self.registry = None
        self.bus = None
        self.voice = None

    def set_wiring(self, registry, bus):
        self.registry, self.bus = registry, bus

    # ───────────────────────── zero-token local intents ─────────────────────────
    def _local(self, text):
        t = text.lower().strip()
        now = datetime.datetime.now()
        if re.search(r"\b(time|clock)\b", t) and len(t.split()) <= 6:
            s = now.strftime("It's %I:%M %p, boss.")
            return {"summary": s, "detail": now.isoformat(), "kind": "local"}
        if re.search(r"\bdate\b", t) and len(t.split()) <= 6:
            s = now.strftime("Today is %A, %B %d, %Y.")
            return {"summary": s, "detail": now.isoformat(), "kind": "local"}
        if t in ("who are you", "what are you", "introduce yourself"):
            return {"summary": "I'm CRYOUS — your multi-agent AI operating system. Voice, research, code, files, "
                               "automation and more, at your command, boss.", "detail": "", "kind": "local"}
        if re.match(r"^(thank you|thanks|cheers)\b", t):
            return {"summary": "Anytime, boss.", "detail": "", "kind": "local"}
        if re.search(r"open (the )?(dashboard|command deck|ui|interface)", t):
            webbrowser.open(f"http://127.0.0.1:{self.cfg.ui_port}")
            return {"summary": "Opening the command deck, boss.", "detail": "", "kind": "local"}
        return None

    def _extract_facts(self, text):
        low = text.lower()
        for pat, key in ((r"my name is ([a-z ]+)", "name"),
                         (r"i (?:prefer|like) ([\w ]{3,60})", "preference"),
                         (r"my (?:favorite|favourite) ([\w ]+) is ([\w ]+)", "favorite")):
            m = re.search(pat, low)
            if m:
                self.db.set_fact(key, m.group(0))
        m = re.search(r"remember that (.+)", low)
        if m:
            self.db.set_fact("note:" + m.group(1)[:30], m.group(1))

    # ───────────────────────── main entry ─────────────────────────
    async def think(self, text, session="ui"):
        self._extract_facts(text)

        loc = self._local(text)
        if loc:
            self.db.add_chat("user", text, session)
            self.db.add_chat("assistant", loc["summary"], session)
            return loc

        # learned skill → zero tokens
        skill = self.db.match_skill(text)
        if skill:
            row, action = skill
            self.db.bump_skill(row["id"])
            if "agent" not in action:
                return {"summary": action.get("reply", "Done, boss."), "detail": "(learned skill)", "kind": "skill"}
            return await self._dispatch({"action": action}, text)

        # self-growth: learn a voice command
        lrn = self.improver.parse_learn(text)
        if lrn:
            trig, act = lrn
            agent = self.registry.pick(act)
            action = {"agent": agent.name, "task": act} if agent else {"reply": act}
            self.improver.learn_command(trig, action)
            return {"summary": f"Learned, boss. When you say '{trig}', I'll handle it instantly — no thinking required.",
                    "detail": json.dumps(action, indent=2), "kind": "skill"}

        # self-growth: forge a whole new plugin
        m = re.search(r"create (?:a )?plugin (?:called |named )?([\w]+)[:\-] ?(.+)", text, re.I)
        if m:
            asyncio.create_task(self._plugin_bg(m.group(1).lower(), m.group(2)))
            return {"summary": f"Forging plugin '{m.group(1)}' in the background, boss. I'll announce it when it's live.",
                    "detail": "", "kind": "plugin"}

        # LLM path
        messages = [{"role": "system", "content": self._system()}] \
                   + self.db.history(self.cfg.max_history) \
                   + [{"role": "user", "content": text}]
        tier = self.router.classify(text)
        out, meta = await self.router.ask(messages, tier=tier,
                                          max_tokens=1000 if tier == "deep" else 500)
        self.db.add_chat("user", text, session)
        self.db.add_chat("assistant", out[:800], session)

        parsed = self._parse_json(out)
        if parsed:
            if parsed.get("plan"):
                return await self._run_plan(parsed, text)
            if parsed.get("action"):
                return await self._dispatch(parsed, text)
        return {"summary": out.strip(), "detail": out.strip(), "kind": "chat", "meta": meta}

    def _system(self):
        facts = "; ".join(self.db.facts(6)) or "none yet"
        names = ", ".join(self.registry.agents.keys())
        return SYS.format(date=datetime.date.today().isoformat(), facts=facts,
                          names=names, agents=self.registry.describe())

    def _parse_json(self, out):
        m = re.search(r"\{.*\}", out, re.S)
        if not m:
            return None
        try:
            d = json.loads(m.group(0))
            if isinstance(d, dict) and ("action" in d or "plan" in d):
                return d
        except Exception:
            pass
        return None

    # ───────────────────────── dispatch ─────────────────────────
    async def _dispatch(self, parsed, original):
        act = parsed.get("action") or {}
        task = act.get("task") or original
        agent = self.registry.get(act.get("agent", "")) or self.registry.pick(task)
        reply = parsed.get("reply") or ""
        if not agent:
            return {"summary": reply or "No agent matches that task, boss.", "detail": "", "kind": "chat"}

        await self.bus.emit("agent", {"agent": agent.name, "status": "started", "task": task})
        if agent.slow:                                   # heavy work never blocks the voice loop
            asyncio.create_task(self._run_bg(agent, task, original, reply))
            return {"summary": reply or f"Understood. The {agent.name} agent is on it in the background.",
                    "detail": "", "kind": agent.name}
        try:
            res = await agent.run(task, context=original)
            await self.bus.emit("agent", {"agent": agent.name, "status": "done"})
            return {"summary": res.get("summary") or reply or "Done, boss.",
                    "detail": res.get("detail", ""), "kind": agent.name,
                    "artifacts": res.get("artifacts", [])}
        except Exception as e:
            await self.bus.emit("agent", {"agent": agent.name, "status": "error", "error": str(e)})
            self.db.audit("agent_error", f"{agent.name}: {e}")
            return {"summary": f"Hit a snag, boss: {e}", "detail": traceback.format_exc(), "kind": "error"}

    async def _run_bg(self, agent, task, original, reply):
        try:
            res = await agent.run(task, context=original)
            await self.bus.emit("agent", {"agent": agent.name, "status": "done"})
            summ = res.get("summary", "finished")
            await self.bus.emit("assistant", {"summary": f"Background task complete — {summ}",
                                              "detail": res.get("detail", ""), "kind": agent.name, "bg": True})
            if self.voice and self.voice.enabled:
                await self.voice.speaker.say(f"Boss, {agent.name} agent finished. {summ}")
        except Exception as e:
            await self.bus.emit("agent", {"agent": agent.name, "status": "error", "error": str(e)})

    # ───────────────────────── multi-step plans ─────────────────────────
    async def _run_plan(self, parsed, original):
        steps = parsed["plan"]
        await self.bus.emit("plan", {"status": "started", "steps": len(steps)})
        asyncio.create_task(self._plan_bg(steps, original, parsed.get("reply", "")))
        return {"summary": parsed.get("reply") or f"Executing a {len(steps)}-step plan in the background, boss.",
                "detail": json.dumps(steps, indent=2), "kind": "plan"}

    async def _plan_bg(self, steps, original, reply):
        results = []
        for i, step in enumerate(steps, 1):
            agent = self.registry.get(step.get("agent", "")) or self.registry.pick(step.get("task", ""))
            await self.bus.emit("plan", {"status": "step", "i": i, "total": len(steps),
                                         "agent": getattr(agent, "name", "?"), "task": step.get("task", "")})
            if not agent:
                results.append(f"{i}. skipped (no agent)")
                continue
            try:
                ctx = original + "\nPrevious results:\n" + "\n".join(results[-3:])
                res = await agent.run(step.get("task", ""), context=ctx)
                results.append(f"{i}. {res.get('summary', 'done')}")
            except Exception as e:
                results.append(f"{i}. error: {e}")
        detail = "\n".join(results)
        await self.bus.emit("plan", {"status": "done"})
        await self.bus.emit("assistant", {"summary": reply or f"Plan complete, boss. {len(steps)} steps delivered.",
                                          "detail": detail, "kind": "plan", "bg": True})
        if self.voice and self.voice.enabled:
            await self.voice.speaker.say(reply or "Plan complete, boss.")

    # ───────────────────────── self-written plugins ─────────────────────────
    async def _plugin_bg(self, name, spec):
        try:
            path = await self.improver.write_plugin(self.router, name, spec)
            from agents import load_plugins
            load_plugins(self.registry, self.registry.ctx)
            msg = f"Plugin '{name}' forged and installed, boss. I just grew a new capability."
            await self.bus.emit("assistant", {"summary": msg,
                                              "detail": path.read_text(encoding="utf-8"),
                                              "kind": "plugin", "bg": True})
            if self.voice and self.voice.enabled:
                await self.voice.speaker.say(msg)
        except Exception as e:
            await self.bus.emit("log", {"msg": f"plugin forge failed: {e}"})