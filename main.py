import os
import sys
import threading
import queue
from controller import MainController
from voice.wake_word import WakeWordDetector
from brain.llm import LLMProvider

# ==================== CONFIGURATION ====================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "your_groq_api_key_here")
VOSK_MODEL_PATH = "model"
# =======================================================

# 1. Thread-safe Queue for inter-thread communication
action_queue = queue.Queue()

def voice_daemon(controller, wake_detector):
    """
    Background daemon function running on a separate thread.
    Continuously listens for the wake word and handles active voice sessions.
    """
    print("\n[Voice Daemon] Online. Listening for 'Cryous'...")
    while True:
        try:
            # 1. Block and listen for wake word 
            if wake_detector.listen_for_wake_word():
                
                # 2. Briefly notify the main UI thread that a voice session is active
                action_queue.put("[SYSTEM: VOICE SESSION INITIATED]")
                
                # 3. Hand control over to the active voice pipeline
                controller.run_active_session()
                
                # 4. Notify UI thread that session has ended
                action_queue.put("[SYSTEM: VOICE SESSION TERMINATED]")

        except Exception as e:
            print(f"\n[VOICE DAEMON ERROR]: {e}")
            print("[System] Attempting recovery and returning to background mode...")

def boot_system():
    print("=" * 50)
    print(" Booting CRYOUS Cognitive Operating System...")
    print("=" * 50)

    if not os.path.exists(VOSK_MODEL_PATH):
        print(f"[ERROR] Vosk model directory not found at: '{VOSK_MODEL_PATH}'")
        print("Please ensure your local Vosk model is placed inside the 'model/' folder.")
        sys.exit(1)

    # 1. Initialize core system components
    controller = MainController(groq_api_key=GROQ_API_KEY, vosk_model_path=VOSK_MODEL_PATH)
    wake_detector = WakeWordDetector(model_path=VOSK_MODEL_PATH)
    engine = LLMProvider()

    # 2. Launch the Voice Daemon on an independent background thread
    voice_thread = threading.Thread(
        target=voice_daemon, 
        args=(controller, wake_detector),
        daemon=True # Daemon threads exit automatically when the main program closes
    )
    voice_thread.start()

    print("\n[System] All modules loaded successfully. Ready.")
    print("System Online. Type 'exit' or 'quit' to terminate.")
    print("-" * 50)

    # 3. The Main Thread (Terminal Chat Interface)
    while True:
        try:
            # Process any pending notifications from the background voice thread
            while not action_queue.empty():
                message = action_queue.get()
                print(f"\n{message}")

            # Grab user input (this normally blocks, but voice_daemon runs independently)
            user_input = input("\nUSER > ")

            if not user_input.strip():
                continue

            # Deterministic System Commands
            if user_input.startswith('/'):
                command = user_input.lower()
                
                if command in ['/exit', '/quit']:
                    print("\nInitiating shutdown sequence. Goodbye.")
                    sys.exit(0)
                
                elif command == '/clear':
                    os.system('cls' if os.name == 'nt' else 'clear')
                    continue 
                
                else:
                    print(f"[SYSTEM] Unrecognized command: '{command}'")
                    continue

            # Generate and print the LLM chat response
            response = engine.generate_chat_response(user_input)
            print(f"CRYOUS > {response}")

        except KeyboardInterrupt:
            print("\n\n[System] Force shutdown detected. Terminating CRYOUS OS...")
            sys.exit(0)
        except Exception as e:
            print(f"\n[MAIN SYSTEM ERROR]: {e}")

if __name__ == "__main__":
    boot_system()