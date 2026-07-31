import customtkinter as ctk
import pystray
from PIL import Image, ImageDraw, ImageTk
import threading
import queue
import sys
import os

class GhostUI:
    def __init__(self):
        # 1. The Master GUI Root (Hidden)
        # This owns the main thread and manages all child windows.
        self.root = ctk.CTk()
        self.root.withdraw() # Hide the main root window immediately
        
        # 2. Thread-Safe Communication Queue
        self.event_queue = queue.Queue()
        
        # Window trackers
        self.output_window = None
        self.chat_window = None
        self.icon = None

        # Start listening for background thread events
        self._process_queue()

    def _process_queue(self):
        """
        The beating heart of the UI. This runs on the Main Thread and constantly 
        checks if background threads (Voice, Groq, Pystray) have requested UI updates.
        """
        try:
            while True:
                # Get task from queue without blocking
                task = self.event_queue.get_nowait()
                action = task.get("action")
                
                if action == "boot_anim":
                    self._render_boot_animation()
                elif action == "show_output":
                    self._render_transparent_output(task.get("text"))
                elif action == "open_chat":
                    self._render_emergency_chat()
                elif action == "update_chat":
                    self._update_chat_history(task.get("text"))
                    
        except queue.Empty:
            pass
        finally:
            # Check the queue again in 50 milliseconds
            self.root.after(50, self._process_queue)

    # ==========================================
    # PUBLIC THREAD-SAFE TRIGGER METHODS
    # (Call these from ANY background thread)
    # ==========================================
    def play_boot_animation(self):
        self.event_queue.put({"action": "boot_anim"})

    def show_transparent_output(self, text: str):
        self.event_queue.put({"action": "show_output", "text": text})

    def open_emergency_chat_threadsafe(self):
        self.event_queue.put({"action": "open_chat"})

    def _safe_chat_update(self, text: str):
        self.event_queue.put({"action": "update_chat", "text": text})

    # ==========================================
    # INTERNAL RENDERING LOGIC (MAIN THREAD ONLY)
    # ==========================================
    def _render_boot_animation(self, gif_path="ui/atom_boot.gif"):
        """Plays the boot animation as a Toplevel child of the root."""
        boot_app = ctk.CTkToplevel(self.root)
        boot_app.overrideredirect(True)
        boot_app.wm_attributes('-transparentcolor', '#000000')
        boot_app.config(bg='#000000')
        boot_app.wm_attributes('-topmost', True)

        screen_width = boot_app.winfo_screenwidth()
        screen_height = boot_app.winfo_screenheight()
        boot_app.geometry(f"400x400+{int(screen_width/2 - 200)}+{int(screen_height/2 - 200)}")

        try:
            img = Image.open(gif_path)
            frames = []
            try:
                while True:
                    frames.append(ImageTk.PhotoImage(img.copy().convert("RGBA")))
                    img.seek(len(frames))
            except EOFError:
                pass

            label = ctk.CTkLabel(boot_app, text="", fg_color="transparent")
            label.pack(expand=True)

            def animate(frame_idx=0, cycles=0):
                if cycles > 2:
                    boot_app.destroy()
                    return
                
                label.configure(image=frames[frame_idx])
                
                next_frame = frame_idx + 1
                next_cycle = cycles
                if next_frame >= len(frames):
                    next_frame = 0
                    next_cycle += 1
                
                # Using root.after for thread-safe timing
                self.root.after(50, animate, next_frame, next_cycle)

            animate()
        except Exception as e:
            print(f"[System] Boot animation skipped: {e}")
            boot_app.destroy()

    def _render_transparent_output(self, text: str):
        """Renders floating text as a Toplevel child."""
        if self.output_window and self.output_window.winfo_exists():
            self.output_window.destroy()

        self.output_window = ctk.CTkToplevel(self.root)
        self.output_window.config(bg='#000000')
        self.output_window.wm_attributes('-transparentcolor', '#000000')
        self.output_window.overrideredirect(True) 
        self.output_window.wm_attributes('-topmost', True)
        
        screen_width = self.output_window.winfo_screenwidth()
        screen_height = self.output_window.winfo_screenheight()
        self.output_window.geometry(f"400x200+{screen_width - 450}+{screen_height - 300}")

        label = ctk.CTkLabel(
            self.output_window, text=text, fg_color="transparent", 
            text_color="#00FFFF", font=("Courier", 16, "bold"), wraplength=380
        )
        label.pack(pady=20, padx=20)

        # Destroy self after 8 seconds
        self.root.after(8000, self.output_window.destroy)

    def _render_emergency_chat(self):
        """Creates the manual override terminal as a Toplevel child."""
        if self.chat_window is not None and self.chat_window.winfo_exists():
            self.chat_window.lift()
            return

        self.chat_window = ctk.CTkToplevel(self.root)
        self.chat_window.title("CRYOUS // Emergency Override Terminal")
        self.chat_window.geometry("800x600")
        ctk.set_appearance_mode("dark")

        top_frame = ctk.CTkFrame(self.chat_window, fg_color="transparent")
        top_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(top_frame, text="Mode:", font=("Courier", 12, "bold")).pack(side="left", padx=5)
        self.mode_dropdown = ctk.CTkOptionMenu(top_frame, values=["Fast-Lane", "Slow-Lane", "Agent-Lane"])
        self.mode_dropdown.pack(side="left", padx=5)

        self.chat_history = ctk.CTkTextbox(self.chat_window, width=780, height=450, font=("Courier", 12))
        self.chat_history.pack(padx=10, pady=5)
        self.chat_history.insert("0.0", "CRYOUS OS [Version 1.0]\nTerminal activated. Ready...\n\n")
        self.chat_history.configure(state="disabled")

        input_frame = ctk.CTkFrame(self.chat_window, fg_color="transparent")
        input_frame.pack(fill="x", padx=10, pady=10)

        self.text_input = ctk.CTkEntry(input_frame, width=650, placeholder_text="Enter command manual override...")
        self.text_input.pack(side="left", padx=5)

        send_btn = ctk.CTkButton(input_frame, text="SEND", width=100, command=self._handle_text_input)
        send_btn.pack(side="right", padx=5)

    def _update_chat_history(self, text: str):
        """Updates the chat window safely on the main thread."""
        if self.chat_window and self.chat_window.winfo_exists():
            self.chat_history.configure(state="normal")
            self.chat_history.insert("end", text)
            self.chat_history.configure(state="disabled")
            self.chat_history.see("end")

    def _handle_text_input(self):
        """Captures input and fires off the AI request in a background thread."""
        user_text = self.text_input.get()
        if not user_text:
            return
        
        self.text_input.delete(0, 'end')
        self._safe_chat_update(f"User: {user_text}\n")
        
        selected_mode = self.mode_dropdown.get()

        def process_request():
            from engine.groq_router import GroqEngine
            ai_engine = GroqEngine()
            
            if "Fast" in selected_mode:
                response = ai_engine.process_fast_lane(user_text)
            elif "Agent" in selected_mode:
                response = ai_engine.process_agent_lane(user_text)
            else:
                response = ai_engine.process_slow_lane(user_text)
            
            # Send the response back to the main thread queue
            self._safe_chat_update(f"CRYOUS: {response}\n\n")

        # LLM Call happens in background, does not freeze UI
        threading.Thread(target=process_request, daemon=True).start()

    # ==========================================
    # BACKGROUND TRAY (PYSTRAY)
    # ==========================================
    def _create_tray_icon(self):
        image = Image.new('RGB', (64, 64), color=(20, 20, 20))
        d = ImageDraw.Draw(image)
        d.text((15, 25), "CR", fill=(0, 255, 0))

        menu = pystray.Menu(
            # Pass the thread-safe queue trigger to the tray icon
            pystray.MenuItem("Emergency Terminal", self.open_emergency_chat_threadsafe),
            pystray.MenuItem("Exit CRYOUS", self._exit_app)
        )
        self.icon = pystray.Icon("CRYOUS", image, "CRYOUS System", menu)
        self.icon.run()

    def start_tray(self):
        """Starts the tray in a background daemon thread."""
        threading.Thread(target=self._create_tray_icon, daemon=True).start()

    def _exit_app(self, icon, item):
        icon.stop()
        os._exit(0)