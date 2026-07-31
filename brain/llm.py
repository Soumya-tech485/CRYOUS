import os
import json
from dotenv import load_dotenv
from groq import Groq

# Import the file reading tool we created
from tools.read_file import read_local_file

class GroqProvider:
    def __init__(self):
        # Load the .env file so we can securely get the API key
        load_dotenv()
        
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("[CRITICAL ERROR] GROQ_API_KEY missing from environment variables.")
            
        # Initialize the Groq client
        self.client = Groq(api_key=api_key)
        
        # Persistent memory/persona
        self.core_identity = "You are CRYOUS, an advanced Cognitive OS. You operate silently in the background. You are helpful, concise, and highly capable."
        
        # --- MEMORY ARCHITECTURE ---
        # Groq/OpenAI format requires a specific dictionary structure
        self.memory = [{"role": "system", "content": self.core_identity}]
        self.max_turns = 10 # Maximum conversation history before forgetting
        
    def _manage_memory(self, new_message: dict):
        """Appends a new message and enforces the FIFO queue limit."""
        self.memory.append(new_message)
        
        # Keep the system prompt at index 0. 
        # (max_turns * 2) accounts for User + Assistant pairs, +1 for the System Prompt.
        while len(self.memory) > (self.max_turns * 2) + 1:
            self.memory.pop(1) # Pop the oldest user message, protecting the system prompt

    def fast_lane(self, user_input: str) -> str:
        """
        Zero-latency execution using Llama 3 8B. 
        Optimized for quick UI updates and voice responses.
        """
        self._manage_memory({"role": "user", "content": user_input})
        
        try:
            response = self.client.chat.completions.create(
                model="llama3-8b-8192",
                messages=self.memory,
                temperature=0.2,
                max_tokens=500
            )
            output = response.choices[0].message.content
            self._manage_memory({"role": "assistant", "content": output})
            return output
        except Exception as e:
            return f"SYSTEM ERROR (Fast Lane): API communication failed. Details: {e}"

    def slow_lane(self, user_input: str) -> str:
        """
        Deep reasoning execution using Llama 3 70B.
        Optimized for complex coding, math, or deep research tasks.
        """
        self._manage_memory({"role": "user", "content": user_input})
        
        try:
            response = self.client.chat.completions.create(
                model="llama3-70b-8192",
                messages=self.memory,
                temperature=0.4, # Slightly higher for creative reasoning
                max_tokens=2048
            )
            output = response.choices[0].message.content
            self._manage_memory({"role": "assistant", "content": output})
            return output
        except Exception as e:
            return f"SYSTEM ERROR (Slow Lane): API communication failed. Details: {e}"

    def agent_lane(self, user_input: str) -> str:
        """
        Tool-calling execution. Allows Groq to trigger local Python functions.
        """
        self._manage_memory({"role": "user", "content": user_input})
        
        # 1. Define the tools available to Groq
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "read_local_file",
                    "description": "Reads the text content of a local file securely.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "The absolute or relative path to the file."
                            }
                        },
                        "required": ["file_path"]
                    }
                }
            }
        ]

        try:
            # 2. Initial request granting the LLM access to tools
            response = self.client.chat.completions.create(
                model="llama3-70b-8192", # 70B is much better at tool calling than 8B
                messages=self.memory,
                tools=tools,
                tool_choice="auto",
                max_tokens=1024
            )

            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            # 3. THE INTERCEPTOR (Tool Execution Logic)
            if tool_calls:
                # Append the AI's tool request to memory
                self.memory.append(response_message)
                
                for tool_call in tool_calls:
                    if tool_call.function.name == "read_local_file":
                        # Parse the JSON arguments provided by Groq
                        function_args = json.loads(tool_call.function.arguments)
                        file_path = function_args.get("file_path")
                        
                        # Execute your actual Python function
                        file_content = read_local_file(file_path)
                        
                        # Append the physical tool output back to memory as a "tool" role
                        self.memory.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": "read_local_file",
                            "content": file_content,
                        })
                
                # 4. Final generation with the tool context included
                final_response = self.client.chat.completions.create(
                    model="llama3-70b-8192",
                    messages=self.memory
                )
                
                output = final_response.choices[0].message.content
                self._manage_memory({"role": "assistant", "content": output})
                return output
            
            # If the LLM decided it didn't need a tool
            elif response_message.content:
                self._manage_memory({"role": "assistant", "content": response_message.content})
                return response_message.content
                
        except Exception as e:
            return f"SYSTEM ERROR (Agent Lane): Tool execution failed. Details: {e}"