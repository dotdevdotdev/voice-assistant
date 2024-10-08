import speech_recognition as sr
import pyttsx3
import openai


class Assistant:
    def __init__(self, api_key):
        self.recognizer = sr.Recognizer()
        self.engine = pyttsx3.init()
        openai.api_key = api_key

    def listen(self):
        with sr.Microphone() as source:
            print("Listening...")
            audio = self.recognizer.listen(source)

        try:
            text = self.recognizer.recognize_google(audio)
            return text
        except sr.UnknownValueError:
            return "Sorry, I couldn't understand that."
        except sr.RequestError:
            return "Sorry, there was an error with the speech recognition service."

    def process(self, user_input):
        response = openai.Completion.create(
            # Replace the deprecated model with a supported one
            model="gpt-3.5-turbo-instruct",  # or another appropriate model
            prompt=user_input,
            # ... other parameters ...
        )
        # ... rest of the method ...

    def speak(self, text):
        self.engine.say(text)
        self.engine.runAndWait()
