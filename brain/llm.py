import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Import the file reading tool we created
from tools.file_ops import read_local_file

class LLMProvider:
    def __init__(self):
        # Load the .env file so we can securely get the API key
        load_dotenv()
        
        # Initialize the Gemini client
        api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key)
        
        # Persistent memory/persona
        self.core_identity = "You are CRYOUS, an advanced Cognitive OS. You are helpful, concise, and highly capable."
        
        # --- MEMORY ARCHITECTURE ---
        self.memory = [] # The FIFO Queue
        self.max_turns = 10 # Maximum conversation history before forgetting
        
    def generate_chat_response(self, user_input: str) -> str:
        try:
            # 1. Set up the configuration with our tool menu
            config = types.GenerateContentConfig(
                system_instruction=self.core_identity,
                temperature=0.2,
                tools=[read_local_file] 
            )
            
            # 2. Append the new user input to the memory queue
            self.memory.append({"role": "user", "parts": [{"text": user_input}]})
            
            # 3. Send the entire memory array to Gemini
            response = self.client.models.generate_content(
                model='gemini-3.5-flash', 
                contents=self.memory,
                config=config
            )

            # 4. THE INTERCEPTOR (Tool Logic)
            if response.function_calls:
                function_call = response.function_calls[0]
                
                if function_call.name == "read_local_file":
                    file_to_read = function_call.args["file_path"]
                    file_content = read_local_file(file_to_read)
                    
                    final_response = self.client.models.generate_content(
                        model='gemini-3.5-flash',
                        contents=f"The user asked to read {file_to_read}. Here is the content: \n{file_content}\n Summarize or explain it to the user.",
                        config=types.GenerateContentConfig(system_instruction=self.core_identity)
                    )
                    
                    # Store the tool response in memory so it remembers the file read
                    self.memory.append({"role": "model", "parts": [{"text": final_response.text}]})
                    
                    # Manage queue size even after a tool call
                    while len(self.memory) > (self.max_turns * 2):
                        self.memory.pop(0)
                        
                    return final_response.text

            # 5. Standard Text Response
            elif response.text:
                # Append the AI's response to memory
                self.memory.append({"role": "model", "parts": [{"text": response.text}]})
                
                # 6. QUEUE MANAGEMENT (Enforcing the mathematical limit)
                # Multiply by 2 because one full turn = 1 user message + 1 model message
                while len(self.memory) > (self.max_turns * 2):
                    self.memory.pop(0) 
                    
                return response.text
                
            else:
                return "System Error: Received an empty response from the AI."

        except Exception as e:
            return f"SYSTEM ERROR: API communication failed. Details: {e}"