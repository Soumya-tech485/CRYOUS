import asyncio
import datetime
import re
import time

from .base import Agent


def _parse_when(text):
    t = text.lower()
    m = re.search(r"in\s+(\d+)\s*(second|sec|minute|min|hour|hr|day)s?", t)
    if m:
        mult = {"sec": 1, "second": 1, "min": 60, "minute": 60, "hr": 3600, "hour": 3600, "day": 86400}
        return time.time() + int(m.group(1)) * mult[m.group(2)]
    m = re.search(r"at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", t)
    if m:
        h, mi, ap = int(m.group(1)), int(m.group(2) or 0), m.group(3)
        if ap == "pm" and h < 12:
            h += 12
        if ap == "am" and h == 12:
            h = 0
        target = datetime.datetime.now().replace(hour=h, minute=mi, second=0, microsecond=0)
        if target <= datetime.datetime.now():
            target += datetime.timedelta(days=1)
        return target.timestamp()
    return time.time() + 600


class ReminderAgent(Agent):
    name = "reminder"
    description = "Reminders, timers and alarms"
    keywords = ["remind", "reminder", "alarm", "timer", "don't forget", "wake me"]

    async def run(self, task, context=""):
        t = task.lower()
        m = re.search(r"(?:remind me to|remind me about|reminder to|remind me)\s+(.+?)(?:\s+in\s+\d|\s+at\s+\d|$)", t)
        what = m.group(1).strip() if m else task
        when = _parse_when(t)
        self.ctx.db.add_reminder(when, what)
        at = datetime.datetime.fromtimestamp(when).strftime("%I:%M %p")
        return self.done(f"Reminder set for {at}, boss: {what}.")


class ReminderService:
    """Runs forever in the background — fires reminders without any wake word."""

    def __init__(self, db, bus, voice):
        self.db, self.bus, self.voice = db, bus, voice

    async def run(self):
        await asyncio.sleep(5)
        while True:
            try:
                for r in self.db.due_reminders():
                    self.db.mark_reminder(r["id"])
                    await self.bus.emit("reminder", {"text": r["text"]})
                    if self.voice and self.voice.enabled:
                        await self.voice.speaker.say(f"Boss, reminder: {r['text']}")
            except Exception as e:
                print("[reminders]", e)
            await asyncio.sleep(20)


AGENT = ReminderAgent