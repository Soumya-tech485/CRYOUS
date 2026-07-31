import os
import io
import wave
import json
import time
import math
import struct
import pyaudio
from vosk import Model, KaldiRecognizer
from config.env import AUDIO_SAMPLE_RATE, AUDIO_CHANNELS, VOSK_MODEL_PATH

class VoiceListener:
    def __init__(self, vosk_model_path: str = VOSK_MODEL_PATH, sample_rate: int = AUDIO_SAMPLE_RATE, channels: int = AUDIO_CHANNELS, chunk_size: int = 1024):
        self.vosk_model_path = vosk_model_path
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.format = pyaudio.paInt16
        self._vosk_model = None

    def _get_vosk_model(self) -> Model:
        if self._vosk_model is None:
            if not os.path.exists(self.vosk_model_path):
                raise FileNotFoundError(f"Vosk model directory not found at: '{self.vosk_model_path}'")
            self._vosk_model = Model(self.vosk_model_path)
        return self._vosk_model

    @staticmethod
    def _calculate_rms(data: bytes) -> float:
        count = len(data) // 2
        if count == 0:
            return 0.0
        try:
            shorts = struct.unpack(f"<{count}h", data)
            sum_squares = sum(s ** 2 for s in shorts)
            return math.sqrt(sum_squares / count)
        except struct.error:
            return 0.0

    def record_command_until_silence(self, threshold: int = 800, silence_duration: float = 1.2, max_duration: float = 20.0) -> io.BytesIO:
        """
        Records audio directly into RAM (BytesIO). No disk I/O.
        Returns the byte buffer ready for Groq Whisper transcription.
        """
        p = pyaudio.PyAudio()
        try:
            stream = p.open(format=self.format, channels=self.channels, rate=self.sample_rate, input=True, frames_per_buffer=self.chunk_size)
        except Exception as e:
            print(f"[Error] Failed to open microphone stream: {e}")
            p.terminate()
            return None

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

                if audio_started and silent_chunks > silence_limit:
                    print("[System] Silence detected. Stopping recording.")
                    break

                if (time.time() - start_time) > max_duration:
                    print("[System] Maximum recording duration reached.")
                    break
        except Exception as e:
            print(f"[Error] Recording interrupted: {e}")
            return None
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()

        if not frames:
            print("[Warning] No audio frames captured.")
            return None

        # Compile directly into a virtual file in RAM
        audio_buffer = io.BytesIO()
        try:
            with wave.open(audio_buffer, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(p.get_sample_size(self.format))
                wf.setframerate(self.sample_rate)
                wf.writeframes(b''.join(frames))
            audio_buffer.name = "command.wav" # Groq API requires a filename attribute
            audio_buffer.seek(0)
            return audio_buffer
        except Exception as e:
            print(f"[Error] Failed to compile RAM buffer: {e}")
            return None

    def listen_for_routing_command(self, timeout: float = 6.0) -> str:
        # (Keep your existing Vosk routing logic here, it is efficient for offline keyword spotting)
        pass