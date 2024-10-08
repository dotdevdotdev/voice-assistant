import speech_recognition as sr
import pyttsx3
import openai
from openai import OpenAI  # Make sure to import OpenAI


class Assistant:
    def __init__(self, api_key):
        self.recognizer = sr.Recognizer()
        self.engine = pyttsx3.init()
        openai.api_key = api_key
        self.client = OpenAI()  # Initialize the OpenAI client

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
        # This function should return a response, but it might be returning None
        # Let's add a basic implementation
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_input},
            ],
        )
        return response.choices[0].message.content

    def speak(self, text):
        self.engine.say(text)
        self.engine.runAndWait()
