import os
from core.groq_engine import GroqPipeline
from voice.listener import record_command_until_silence, listen_for_routing_command
from voice.speaker import Speaker

class MainController:
    def __init__(self, groq_api_key: str, vosk_model_path: str):
        # 1. Initialize the Groq processing engine (STT and LLM)
        self.ai_engine = GroqPipeline(api_key=groq_api_key)
        
        # 2. Initialize your modular Speaker
        self.speaker = Speaker(rate=170)
        
        # 3. Store the path for the offline routing listener
        self.vosk_model_path = vosk_model_path

    def display_ui(self, full_text: str):
        """Displays the complete detailed text on your screen/UI."""
        print("\n" + "="*50)
        print(" [CRYOUS UI - FULL OUTPUT] ")
        print(f" {full_text}")
        print("="*50 + "\n")

    def process_text_input(self, user_text: str) -> str:
        """
        Processes manual CLI/UI text chat input through the Groq pipeline.
        Allows main.py to handle text interactions seamlessly.
        """
        try:
            response_data = self.ai_engine.generate_response(user_text)
            if isinstance(response_data, dict):
                return response_data.get("full_details", response_data.get("summary", "Done."))
            return str(response_data)
        except Exception as e:
            return f"[ERROR]: Failed to process request - {e}"

    def run_active_session(self):
        """
        The active voice loop. Triggered by wake word detection in main.py.
        """
        print("\n[System] Active Voice Mode Started.")
        self.speaker.speak("Yes boss, do you need any help?")
        
        while True:
            audio_file = None
            try:
                # 1. Record what you say until you stop speaking
                audio_file = record_command_until_silence()
                
                # 2. Convert audio to text using Groq Whisper
                user_text = self.ai_engine.transcribe(audio_file)
                print(f"[System] Heard: '{user_text}'")
                
            except Exception as e:
                print(f"[System Error] Audio capture/transcription failed: {e}")
                self.speaker.speak("Sorry boss, I didn't catch that.")
                user_text = ""
            finally:
                # Clean up the temporary audio file safely
                if audio_file and os.path.exists(audio_file):
                    try:
                        os.remove(audio_file)
                    except OSError:
                        pass
                
            # Check if you said "nothing" or remained silent to cancel
            if not user_text or "nothing" in user_text.lower():
                print("[System] Aborting. Going back to sleep.")
                return

            # 3. Get the structured response from Groq Llama-3
            try:
                response_data = self.ai_engine.generate_response(user_text)
                summary = response_data.get("summary", "Done, boss.")
                full_details = response_data.get("full_details", "No details provided.")
            except Exception as e:
                print(f"[System Error] Groq generation failed: {e}")
                summary = "I encountered an error processing that request."
                full_details = f"Error details: {e}"
            
            # 4. Show the full details and speak the short summary
            self.display_ui(full_details)
            self.speaker.speak(summary)
            
            # 5. Ask if more help is needed and route based on your answer
            while True:
                self.speaker.speak("Any other help needed, boss?")
                
                action = listen_for_routing_command(self.vosk_model_path)
                
                if action == "wait":
                    print("[System] Waiting for your next command...")
                    break 
                
                elif action == "repeat":
                    print("[System] Repeating the summary...")
                    self.speaker.speak(summary)
                    
                elif action == "no":
                    print("[System] Shutting down active mode. Returning to background.")
                    return
                
                else:
                    print("[System] Unrecognized routing command. Exiting active session.")
                    return