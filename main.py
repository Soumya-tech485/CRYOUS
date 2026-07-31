import os
import sys
import threading
import time

# ==================== NEW ARCHITECTURE IMPORTS ====================
from core.system_boot import add_cryous_to_startup
from ui.ghost_interface import GhostUI
from engine.groq_router import GroqEngine

# Assuming these are updated to thread-safe versions from our earlier steps
from voice.speaker import Speaker
from voice.listener import Listener
# ==================================================================

class CryousOS:
    def __init__(self):
        print("=" * 50)
        print(" Booting CRYOUS Autonomous Operating System...")
        print("=" * 50)
        
        # 1. Register for Windows Startup (Silent Boot)
        add_cryous_to_startup()

        # 2. Initialize UI, AI Routing Engine, and Audio Subsystems
        try:
            self.ui = GhostUI()
            self.engine = GroqEngine()
            self.speaker = Speaker()
            self.listener = Listener()
        except Exception as e:
            print(f"[CRITICAL ERROR] Failed to initialize core subsystems: {e}")
            sys.exit(1)

        self.is_running = True

    def boot_sequence(self):
        """Executes startup splash animation and voice greeting without blocking."""
        # Start System Tray in a background thread to keep it alive
        self.ui.start_tray()

        # Play the hologram boot animation (Auto-destroys after 3s)
        self.ui.play_boot_animation()

        # Silent background greeting
        self.speaker.speak("Hello Boss. CRYOUS is online.")

    def voice_daemon(self):
        """
        Background daemon function running on a separate thread.
        Continuously listens for the wake word 'cryous' and handles active voice sessions.
        """
        print("\n[Voice Daemon] Online. Passive listener active...")
        
        while self.is_running:
            try:
                # 1. Continuous passive capture (non-blocking to system)
                audio_text = self.listener.listen_passive()
                
                if not audio_text:
                    continue

                # 2. Check for the wake word
                if "cryous" in audio_text.lower():
                    print("\n[SYSTEM: VOICE SESSION INITIATED]")
                    
                    # Acknowledge the user
                    self.speaker.speak("Yes boss, do you need any help?")

                    # Active listen for the specific user command
                    command = self.listener.listen_active()

                    if command:
                        print(f"[User Input] Captured: '{command}'")
                        
                        # VITAL FIX: Fire off the brain in a separate thread so the ears don't go deaf.
                        threading.Thread(
                            target=self._process_command, 
                            args=(command,), 
                            daemon=True
                        ).start()
                    else:
                        print("[System] No speech detected after wake word.")
                    
                    print("[SYSTEM: VOICE DAEMON RETURNED TO PASSIVE STANDBY]\n")

            except Exception as e:
                print(f"\n[VOICE DAEMON ERROR]: {e}")
                print("[System] Attempting recovery and returning to passive mode...")
                time.sleep(1)

    def _process_command(self, command: str):
        """
        Routes the recognized command through the Groq lanes.
        Runs entirely in an isolated thread to maintain OS responsiveness.
        """
        command_lower = command.lower()

        # Route based on explicit keywords
        if "agent" in command_lower or "use tools" in command_lower or "search" in command_lower or "screen" in command_lower:
            self.speaker.speak("Engaging autonomous tools, boss.")
            response = self.engine.process_agent_lane(command)
            
        elif "deep research" in command_lower or "slow lane" in command_lower:
            self.speaker.speak("Initiating deep research protocol.")
            response = self.engine.process_slow_lane(command)
            
        else:
            # Default to Fast-Lane for zero-latency conversational responses
            response = self.engine.process_fast_lane(command)

        # Notify audio completion immediately
        self.speaker.speak("Boss, the given work is done.")

        # Push to UI. (Ensure GhostUI's show_transparent_output handles thread-safety internally 
        # using .after() if it relies on CustomTkinter/Tkinter mainloop)
        self.ui.show_transparent_output(response)

    def start(self):
        """Ignites the OS logic."""
        # 1. Run visuals & greeting
        self.boot_sequence()

        # 2. Launch the Voice Daemon on an independent background thread
        voice_thread = threading.Thread(target=self.voice_daemon, daemon=True)
        voice_thread.start()

        print("\n[System] All modules loaded successfully. Ready.")
        print("[System] CRYOUS is running silently in the taskbar.")
        print("-" * 50)


if __name__ == "__main__":
    app = CryousOS()
    app.start()

    # 3. GUI Main Thread Takeover
    # The UI root mainloop replaces the while/sleep loop.
    try:
        app.ui.root.mainloop()
    except KeyboardInterrupt:
        print("\n\n[System] Force shutdown detected. Terminating CRYOUS OS...")
        sys.exit(0)