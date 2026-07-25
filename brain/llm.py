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
        
        # This is the persistent memory/persona we set up earlier
        self.core_identity = "You are CRYOUS, an advanced Cognitive OS. You are helpful, concise, and highly capable."
       
    def generate_chat_response(self, user_input: str) -> str:
        try:
            # 1. Set up the configuration with our tool menu
            config = types.GenerateContentConfig(
                system_instruction=self.core_identity,
                temperature=0.2,
                tools=[read_local_file] # The AI can now see this tool
            )
            
            # 2. Send the user's message to Gemini
            response = self.client.models.generate_content(
                model='gemini-3.5-flash', 
                contents=user_input,
                config=config
            )

            # 3. THE INTERCEPTOR (The If/Else Logic)
            
            # IF condition: Did the AI ask to use a tool?
            if response.function_calls:
                # Get the details of the tool the AI wants to use
                function_call = response.function_calls[0]
                
                # Check if it's our file reading tool
                if function_call.name == "read_local_file":
                    # Get the file name the AI wants to read (e.g., "main.py")
                    file_to_read = function_call.args["file_path"]
                    
                    # RUN OUR LOCAL PYTHON FUNCTION
                    file_content = read_local_file(file_to_read)
                    
                    # Send this text back to Gemini so it can read it and answer the user
                    final_response = self.client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=f"The user asked to read {file_to_read}. Here is the content: \n{file_content}\n Summarize or explain it to the user.",
                        config=types.GenerateContentConfig(system_instruction=self.core_identity)
                    )
                    return final_response.text

            # ELSE condition: It's just a normal text response
            elif response.text:
                return response.text
                
            else:
                return "System Error: Received an empty response from the AI."

        except Exception as e:
            return f"SYSTEM ERROR: API communication failed. Details: {e}"