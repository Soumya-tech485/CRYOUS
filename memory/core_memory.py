import json
import os
from collections import deque
from typing import Dict, Any, List

class MemoryManager:
    def __init__(self, workspace_dir: str = "data/workspace"):
        self.ledger_file = os.path.join(workspace_dir, "reflexion_ledger.json")
        os.makedirs(workspace_dir, exist_ok=True)
        
        # --- TIER 3: The Anchor (Permanent Rules) ---
        self.reflexion_ledger = self._load_json(self.ledger_file, default=[])
        
        # --- TIER 2: The Dynamic Thread (Strict 3-Step Window) ---
        # deque automatically drops the oldest item when maxlen is exceeded
        self.action_window = deque(maxlen=3)
        
        # --- TIER 1: The Exact State (Now) ---
        self.current_state = {
            "objective": "",
            "current_error": None
        }

    def _load_json(self, path: str, default: Any) -> Any:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return default
        return default

    def _save_json(self, path: str, data: Any):
        with open(path, 'w') as f:
            json.dump(data, f, indent=4)

    # --- STATE UPDATES (Fixing the old append issue) ---

    def log_action(self, action_desc: str, result_desc: str):
        """Pushes a new action into the 3-step window. Oldest is destroyed."""
        self.action_window.append({
            "action": action_desc,
            "result": result_desc
        })

    def set_current_state(self, objective: str = None, error: str = None):
        """Strictly overwrites the current environment state."""
        if objective:
            self.current_state["objective"] = objective
        if error is not None:  # Allow clearing the error with empty string
            self.current_state["current_error"] = error

    def add_reflexion_rule(self, rule: str):
        """Saves a hard lesson permanently to the ledger."""
        if rule not in self.reflexion_ledger:
            self.reflexion_ledger.append(rule)
            self._save_json(self.ledger_file, self.reflexion_ledger)

    # --- PAYLOAD GENERATION ---

    def build_dynamic_payload(self) -> str:
        """
        Constructs the ultra-lightweight prompt for the LLM. 
        This replaces sending the entire chat history.
        """
        payload = f"OBJECTIVE: {self.current_state['objective']}\n\n"
        
        payload += "RECENT ACTIONS (Sliding Window):\n"
        if not self.action_window:
            payload += "  - No previous actions in current window.\n"
        else:
            for i, step in enumerate(self.action_window, start=1):
                payload += f"  - t-{len(self.action_window) - i + 1}: [Action: {step['action']} | Result: {step['result']}]\n"
        
        if self.current_state["current_error"]:
            payload += f"\nCURRENT ERROR/OUTPUT:\n{self.current_state['current_error']}\n"
            
        return payload