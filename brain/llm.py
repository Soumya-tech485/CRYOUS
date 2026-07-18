# brain/llm.py
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

class LLMProvider:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model_name = "gemini-3.5-flash"
        
        # --- NEW: Define the permanent system identity ---
        self.core_identity = """
        You are CRYOUS, a Cognitive Operating System developed in Python. 
        You interface with users via a terminal. 
        Keep your responses analytical, concise, and highly technical. 
        Do not use emojis. Prioritize logic over pleasantries.
        """

    def generate_chat_response(self, conversation_history: list) -> str:
        try:
            contents = []
            for turn in conversation_history:
                role = "user" if turn["role"] == "user" else "model"
                contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part.from_text(text=turn["content"])]
                    )
                )

            # --- NEW: Inject the configuration bypassing the history array ---
            config = types.GenerateContentConfig(
                system_instruction=self.core_identity,
                # We can also add parameters here like temperature (creativity level)
                temperature=0.2 
            )

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config # Pass the config to the engine
            )
            return response.text
        except Exception as e:
            return f"CRYOUS: Brain connection failed. Error: {str(e)}"