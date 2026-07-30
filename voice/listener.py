import os
import wave
import json
import time
import math
import struct
import pyaudio
from vosk import Model, KaldiRecognizer

class VoiceListener:
    def __init__(
        self,
        vosk_model_path: str = "model",
        sample_rate: int = 16000,
        channels: int = 1,
        chunk_size: int = 1024
    ):
        """
        Initializes the VoiceListener with audio parameters and Vosk model configuration.
        """
        self.vosk_model_path = vosk_model_path
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.format = pyaudio.paInt16
        self._vosk_model = None

    def _get_vosk_model(self) -> Model:
        """Lazy-loads the Vosk model on first use."""
        if self._vosk_model is None:
            if not os.path.exists(self.vosk_model_path):
                raise FileNotFoundError(f"Vosk model directory not found at path: '{self.vosk_model_path}'")
            self._vosk_model = Model(self.vosk_model_path)
        return self._vosk_model

    @staticmethod
    def _calculate_rms(data: bytes) -> float:
        """
        Calculates Root Mean Square (RMS) volume level for 16-bit PCM audio chunks.
        Replaces 'audioop.rms' to preserve compatibility with Python 3.13+.
        """
        count = len(data) // 2
        if count == 0:
            return 0.0
        shorts = struct.unpack(f"{count}h", data)
        sum_squares = sum(s ** 2 for s in shorts)
        return math.sqrt(sum_squares / count)

    def record_command_until_silence(
        self,
        output_filename: str = "temp_command.wav",
        threshold: int = 800,
        silence_duration: float = 1.2,
        max_duration: float = 20.0
    ) -> str:
        """
        Records audio from the microphone until silence is detected or max_duration is reached.
        Saves captured PCM stream as a WAV file for Groq Whisper transcription.
        """
        p = pyaudio.PyAudio()
        try:
            stream = p.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
        except Exception as e:
            print(f"[Error] Failed to open microphone stream: {e}")
            p.terminate()
            return ""

        print("\n[System] Recording command... (Speak now)")

        frames = []
        silent_chunks = 0
        audio_started = False
        silence_limit = int((self.sample_rate / self.chunk_size) * silence_duration)
        start_time = time.time()

        try:
            while True:
                data = stream.read(self.chunk_size, exception_on_overflow=False)
                frames.append(data)

                rms = self._calculate_rms(data)

                if rms > threshold:
                    audio_started = True
                    silent_chunks = 0
                elif audio_started:
                    silent_chunks += 1

                # Stop recording when silence threshold duration is reached
                if audio_started and silent_chunks > silence_limit:
                    print("[System] Silence detected. Stopping recording.")
                    break

                # Hard timeout guard
                if (time.time() - start_time) > max_duration:
                    print("[System] Maximum recording duration reached.")
                    break

        except Exception as e:
            print(f"[Error] Recording interrupted: {e}")
            return ""
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()

        if not frames:
            print("[Warning] No audio frames captured.")
            return ""

        # Write captured frames to WAV
        try:
            with wave.open(output_filename, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(pyaudio.PyAudio().get_sample_size(self.format))
                wf.setframerate(self.sample_rate)
                wf.writeframes(b''.join(frames))
            return output_filename
        except Exception as e:
            print(f"[Error] Failed to save WAV file: {e}")
            return ""

    def listen_for_routing_command(self, timeout: float = 6.0) -> str:
        """
        Uses offline Vosk with restricted grammar to rapidly detect follow-up routing 
        choices ('wait', 'repeat', 'no') without making Groq API requests.
        """
        try:
            model = self._get_vosk_model()
        except Exception as e:
            print(f"[Error] Vosk initialization failed: {e}")
            return "no"

        CHUNK = 4000
        p = pyaudio.PyAudio()

        try:
            stream = p.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=8000
            )
        except Exception as e:
            print(f"[Error] Failed to open Vosk audio stream: {e}")
            p.terminate()
            return "no"

        # Restrict grammar strictly to target options for instant low-latency evaluation
        grammar = '["wait", "repeat", "no", "nothing", "[unk]"]'
        rec = KaldiRecognizer(model, self.sample_rate, grammar)

        print("[System] Listening for routing command: 'wait', 'repeat', or 'no'...")

        # Clear buffer to ignore residual audio
        try:
            stream.read(stream.get_read_available(), exception_on_overflow=False)
        except Exception:
            pass

        command = "no"
        start_time = time.time()

        try:
            while True:
                # Timeout safeguard if user does not respond
                if (time.time() - start_time) > timeout:
                    print("[System] Routing window timed out. Defaulting to 'no'.")
                    break

                data = stream.read(CHUNK, exception_on_overflow=False)
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    text = result.get("text", "")

                    if text:
                        print(f"[System] Routing Command Heard: '{text}'")
                        if "wait" in text:
                            command = "wait"
                            break
                        elif "repeat" in text:
                            command = "repeat"
                            break
                        elif "no" in text or "nothing" in text:
                            command = "no"
                            break
        except Exception as e:
            print(f"[Error] Vosk recognition error: {e}")
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()

        return command


# --- Standalone Function Wrappers (Preserves Compatibility) ---

_default_listener = VoiceListener()

def record_command_until_silence(output_filename="temp_command.wav", threshold=800, silence_duration=1.2):
    return _default_listener.record_command_until_silence(
        output_filename=output_filename,
        threshold=threshold,
        silence_duration=silence_duration
    )

def listen_for_routing_command(vosk_model_path="../model"):
    listener = VoiceListener(vosk_model_path=vosk_model_path)
    return listener.listen_for_routing_command()