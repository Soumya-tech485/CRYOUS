import pyaudio
import wave
import audioop
import json
from vosk import Model, KaldiRecognizer

def record_command_until_silence(output_filename="temp_command.wav", threshold=800, silence_duration=1.2):
    """
    Records audio from the microphone until silence is detected.
    Saves it as a WAV file to be sent to Groq.
    """
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

    print("\n[System] Recording command... (Speak now)")

    frames = []
    silent_chunks = 0
    audio_started = False
    silence_limit = int((RATE / CHUNK) * silence_duration)

    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)
        
        rms = audioop.rms(data, 2)
        
        if rms > threshold:
            audio_started = True
            silent_chunks = 0
        elif audio_started:
            silent_chunks += 1
            
        if audio_started and silent_chunks > silence_limit:
            break

    print("[System] Silence detected. Stopping recording.")

    stream.stop_stream()
    stream.close()
    p.terminate()

    with wave.open(output_filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        
    return output_filename

def listen_for_routing_command(vosk_model_path="../model"):
    """
    The follow-up routing function. Uses offline Vosk to listen for
    'wait', 'repeat', or 'no' without wasting Groq API calls.
    """
    CHUNK = 4000
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=8000)
    
    # Load the Vosk model locally
    model = Model(vosk_model_path)
    
    # Restrict grammar strictly to these commands for instant recognition
    grammar = '["wait", "repeat", "no", "nothing", "[unk]"]'
    rec = KaldiRecognizer(model, RATE, grammar)
    
    print("[System] Listening for: 'wait', 'repeat', or 'no'...")
    
    # Flush buffer to ensure we don't process leftover audio
    stream.read(stream.get_read_available(), exception_on_overflow=False) 

    command = "no" # Default to 'no' if something fails

    try:
        while True:
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
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

    return command