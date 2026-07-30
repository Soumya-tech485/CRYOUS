import json
import os
from collections import deque
from typing import Dict

class MemoryManager:
    def __init__(self, max_history=3, ledger_path="reflexion_ledger.json"):
        self.max_history = max_history
        self.ledger_path = ledger_path
        self.action_history = deque(maxlen=self.max_history)
        self.current_state = {"objective": "", "error": ""}
        self.reflexion_ledger = self._load_ledger()

    def _load_ledger(self) -> list:
        if os.path.exists(self.ledger_path):
            with open(self.ledger_path, 'r') as f:
                return json.load(f)
        return []

    def save_to_ledger(self, lesson: str):
        if lesson not in self.reflexion_ledger:
            self.reflexion_ledger.append(lesson)
            with open(self.ledger_path, 'w') as f:
                json.dump(self.reflexion_ledger, f, indent=4)

    def set_current_state(self, objective: str = None, error: str = None):
        if objective is not None:
            self.current_state["objective"] = objective
        if error is not None:
            self.current_state["error"] = error

    def log_action(self, action_desc: str, result_desc: str):
        self.action_history.append({"action": action_desc, "result": result_desc})

    def build_dynamic_payload(self) -> str:
        payload = f"CURRENT OBJECTIVE:\n{self.current_state['objective']}\n\n"
        
        if self.action_history:
            payload += "RECENT ACTIONS (Last 3 Steps):\n"
            for idx, entry in enumerate(self.action_history, 1):
                payload += f"Step {idx}: {entry['action']} -> {entry['result']}\n"
        
        if self.current_state["error"]:
            payload += f"\nACTIVE ERROR STATE:\n{self.current_state['error']}\n"
            
        return payload