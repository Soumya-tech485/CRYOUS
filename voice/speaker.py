import pyttsx3

class Speaker:
    def __init__(self, rate: int = 170):
        """Initializes the Text-to-Speech engine."""
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', rate)
        
        # Optional: You can configure voices here if you want to change CRYOUS's accent
        # voices = self.engine.getProperty('voices')
        # self.engine.setProperty('voice', voices[0].id) # 0 for male, 1 for female usually

    def speak(self, text: str):
        """Processes the text string and outputs it as speech."""
        if text:
            self.engine.say(text)
            self.engine.runAndWait()