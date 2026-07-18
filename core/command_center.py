# core/command_center.py
from brain.llm import LLMProvider

class CommandCenter:
    def __init__(self):
        self.brain = LLMProvider()
        self.history = []
        # Define the maximum number of conversation turns to remember
        self.max_memory_length = 10 

    def execute_command(self, user_input: str) -> str:
        
        # 1. System Command Intercept
        if user_input.startswith('/'):
            return self._handle_system_command(user_input)
            
        # 2. Append new input
        self.history.append({"role": "user", "content": user_input})
        
        # --- THE NEW LOGIC: THE SLIDING WINDOW ---
        # If our history exceeds the limit, trim the oldest messages
        if len(self.history) > self.max_memory_length:
            # Keep only the last 'max_memory_length' items
            self.history = self.history[-self.max_memory_length:]
            print(f"[DEBUG] Memory trimmed to last {self.max_memory_length} interactions.")
        
        print("[INFO] Routing context-enriched query to AI Engine...")
        
        # 3. Route to AI
        system_response = self.brain.generate_chat_response(self.history)
        
        # 4. Append AI response
        self.history.append({"role": "assistant", "content": system_response})
        
        return system_response

    def _handle_system_command(self, command: str) -> str:
        # (Keep your existing _handle_system_command code here exactly as it is)
        cmd_parts = command.strip().lower().split()
        base_cmd = cmd_parts[0]

        if base_cmd == '/status':
            return f"SYSTEM STATUS: Online.\nMemory Buffer: {len(self.history)}/{self.max_memory_length} active context turns."
        elif base_cmd == '/clear':
            self.history.clear()
            return "SYSTEM MEMORY CLEARED: Context buffer reset to zero."
        elif base_cmd == '/help':
            return "AVAILABLE COMMANDS:\n/status - Check system health & memory size\n/clear - Reset memory buffer\n/help - Show this menu\nexit - Shutdown CRYOUS"
        else:
            return f"ERROR: Unrecognized system command '{base_cmd}'."