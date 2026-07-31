import os
import json
from groq import Groq
from config.env import GROQ_API_KEY

# --- Live Tool Imports ---
from research.search import web_search
from tools.vision import analyze_screen
from tools.file_ops import read_file, write_local_file

class GroqEngine:
    def __init__(self):
        """Initializes the Groq client and defines the model stack with Agent capabilities."""
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is missing from environment variables.")
        
        self.client = Groq(api_key=GROQ_API_KEY)
        
        # Fast-Lane: Blisteringly fast. Perfect for quick conversational tasks.
        self.fast_model = "llama3-8b-8192" 
        
        # Slow-Lane / Agent-Lane: Handles complex reasoning, master prompts, and tool calling.
        self.slow_model = "llama3-70b-8192"

        # Define the tools available to CRYOUS
        self.available_tools = [
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Searches the live internet for up-to-date information when you don't know the answer.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "The search query to look up on the web."}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_screen",
                    "description": "Captures the user's screen silently to analyze what they are looking at, translate text, or explain UI.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "prompt": {"type": "string", "description": "What to look for on the screen."}
                        },
                        "required": ["prompt"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Reads the text content of a local file or PDF on the user's system.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filepath": {"type": "string", "description": "The absolute or relative path to the file."}
                        },
                        "required": ["filepath"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "write_local_file",
                    "description": "Writes text or code to a local file within the secure sandbox staging area. Can utilize matrix-cipher encryption.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filepath": {"type": "string", "description": "The target filename or path within the sandbox."},
                            "content": {"type": "string", "description": "The exact content, code, or data to write to the file."},
                            "encrypt": {"type": "boolean", "description": "Set to true to encrypt the file using the local matrix cipher before saving."}
                        },
                        "required": ["filepath", "content"]
                    }
                }
            }
        ]

    def process_fast_lane(self, user_text: str) -> str:
        """Instant execution. No routing, no tools. Pure speed."""
        try:
            print("[System] Routing: FAST-LANE")
            response = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system", 
                        "content": (
                            "You are CRYOUS, a highly efficient autonomous AI OS. "
                            "Respond as quickly, concisely, and accurately as possible. "
                            "Do not show your work. Output ONLY the final, actionable answer."
                        )
                    },
                    {"role": "user", "content": user_text}
                ],
                model=self.fast_model,
                temperature=0.3,
                max_tokens=256,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            error_msg = f"System error in Fast-Lane execution: {e}"
            print(f"[Error] {error_msg}")
            return error_msg

    def process_slow_lane(self, user_text: str) -> str:
        """Deep research execution generating a Master Prompt first."""
        print("\n[System] Routing: SLOW-LANE (Deep Research Engaged)")
        
        print("[System] Phase 1: Synthesizing Master Prompt...")
        try:
            router_response = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system", 
                        "content": (
                            "You are the CRYOUS routing engine. The user has a complex task. "
                            "Rewrite their request into a highly detailed, optimal 'master prompt' "
                            "designed to extract the best possible answer from a Large Language Model. "
                            "Output ONLY the master prompt text."
                        )
                    },
                    {"role": "user", "content": user_text}
                ],
                model=self.fast_model, 
                temperature=0.1,
                max_tokens=512,
            )
            master_prompt = router_response.choices[0].message.content.strip()
            print(f"[System] Master Prompt Generated:\n{'-'*40}\n{master_prompt}\n{'-'*40}")
        except Exception as e:
            print(f"[Error] Master prompt generation failed: {e}")
            return "System error during master prompt generation."

        print("[System] Phase 2: Executing via Heavy Model...")
        try:
            final_response = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system", 
                        "content": (
                            "You are CRYOUS, operating in Slow-Lane Deep Research mode. "
                            "Execute the user's master prompt flawlessly. "
                            "Do not include the internal steps unless explicitly asked."
                        )
                    },
                    {"role": "user", "content": master_prompt}
                ],
                model=self.slow_model,
                temperature=0.6,
                max_tokens=2048,
            )
            return final_response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[Error] Slow-Lane execution failed: {e}")
            return "System error during deep research execution."

    def process_agent_lane(self, user_text: str) -> str:
        """
        Autonomous Agent execution. Gives the LLM access to external tools (Search, Vision, Files).
        Loops until the LLM has all the data it needs to formulate a final response.
        """
        print("\n[System] Routing: AGENT-LANE (Tool Calling Engaged)")
        
        messages = [
            {
                "role": "system",
                "content": (
                    "You are CRYOUS, an autonomous AI OS. You have access to tools to interact "
                    "with the user's system and the internet. Use them if necessary to fulfill the request. "
                    "If you use a tool, wait for the result before giving your final answer to the user."
                )
            },
            {"role": "user", "content": user_text}
        ]

        try:
            # Step 1: Initial call to see if the LLM wants to use a tool
            response = self.client.chat.completions.create(
                model=self.slow_model,
                messages=messages,
                tools=self.available_tools,
                tool_choice="auto",
                temperature=0.2,
                max_tokens=1024
            )
            
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            # Step 2: If no tools are called, return the standard response
            if not tool_calls:
                return response_message.content.strip()

            # Step 3: If tools ARE called, execute them locally
            messages.append(response_message) # Add the model's tool request to conversation history

            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                print(f"[Agent] Triggering Tool: {function_name} with args {function_args}")
                
                # Execute the actual Python logic
                tool_result = self._execute_tool_logic(function_name, function_args)
                print(f"[Agent] Tool Result: {tool_result[:100]}...") # Print first 100 chars
                
                # Append the result back into the message history
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": str(tool_result),
                })

            # Step 4: Final call with the newly acquired data from the tools
            print("[Agent] Re-evaluating with new data...")
            final_response = self.client.chat.completions.create(
                model=self.slow_model,
                messages=messages,
                temperature=0.5,
                max_tokens=2048
            )
            
            return final_response.choices[0].message.content.strip()

        except Exception as e:
            print(f"[Error] Agent-Lane execution failed: {e}")
            return "System error during tool execution."

    def _execute_tool_logic(self, name: str, args: dict) -> str:
        """Internal router to map LLM tool requests to your actual Python files."""
        try:
            if name == "web_search":
                return web_search(args.get("query", ""))
            
            elif name == "analyze_screen":
                return analyze_screen(args.get("prompt", ""))
                
            elif name == "read_file":
                return read_file(args.get("filepath", ""))
                
            elif name == "write_local_file":
                return write_local_file(
                    filepath=args.get("filepath", ""), 
                    content=args.get("content", ""),
                    encrypt=args.get("encrypt", False)
                )
            
            else:
                return f"Error: Tool '{name}' is not recognized by the system."
                
        except Exception as e:
            return f"Error executing tool {name}: {str(e)}"