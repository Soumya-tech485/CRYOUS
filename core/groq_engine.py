import os
import json
from groq import Groq

class GroqPipeline:
    def __init__(self, api_key: str):
        # Initialize the Groq client
        self.client = Groq(api_key=api_key)
        self.stt_model = "whisper-large-v3"
        
        # Using 8b for maximum speed. You can change to 70b if you need heavier logic.
        self.llm_model = "llama3-8b-8192" 

    def transcribe(self, audio_file_path: str) -> str:
        """Sends the recorded WAV file to Groq Whisper for instant transcription."""
        print("[System] Uploading audio to Groq Whisper...")
        try:
            with open(audio_file_path, "rb") as file:
                transcription = self.client.audio.transcriptions.create(
                  file=(audio_file_path, file.read()),
                  model=self.stt_model,
                )
            return transcription.text
        except Exception as e:
            print(f"[Error] Transcription failed: {e}")
            return ""

    def generate_response(self, user_text: str) -> dict:
        """Sends the transcribed text to Llama-3 and forces a JSON return."""
        print("[System] Generating response via Groq Llama-3...")
        
        system_prompt = """
        You are CRYOUS, an advanced AI system. 
        Your primary directive is speed and accuracy. 
        You MUST respond in strictly valid JSON format containing exactly these two keys:
        1. "summary": A very brief, direct, 1-2 sentence spoken summary of what you did.
        2. "full_details": The complete detailed output, code blocks, or extensive explanation.
        """
        
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text}
                ],
                model=self.llm_model,
                response_format={"type": "json_object"} # Forces the AI to return clean JSON
            )
            
            # Parse the JSON string into a Python dictionary
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"[Error] Generation failed: {e}")
            return {"summary": "I encountered an error connecting to the Groq server, boss.", "full_details": str(e)}