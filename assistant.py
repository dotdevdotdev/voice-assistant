import openai
import speech_recognition as sr
import logging
import requests
import io
from pydub import AudioSegment
from pydub.playback import play as pydub_play


class Assistant:
    def __init__(
        self,
        openai_api_key,
        elevenlabs_api_key,
        openai_settings,
        elevenlabs_settings,
        realtime_mode=False,
    ):
        self.recognizer = sr.Recognizer()
        openai.api_key = openai_api_key
        self.client = openai.OpenAI()
        self.elevenlabs_api_key = elevenlabs_api_key

        self.openai_model = openai_settings["model"]
        self.system_prompt = openai_settings["system_prompt"]

        self.elevenlabs_model_id = elevenlabs_settings["model_id"]
        self.voice_id = elevenlabs_settings["voice_id"]
        self.elevenlabs_voice_settings = elevenlabs_settings["voice_settings"]
        self.realtime_mode = realtime_mode
        self.device_found = False

        # Configure logging
        logging.basicConfig(level=logging.WARNING)
        logging.getLogger("speech_recognition").setLevel(logging.ERROR)

    def listen(self):
        with sr.Microphone() as source:
            print("Listening...")
            audio = self.recognizer.listen(source)

        try:
            text = self.recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text
        except sr.UnknownValueError:
            print("Sorry, I couldn't understand that.")
            return "Sorry, I couldn't understand that."
        except sr.RequestError:
            print("Sorry, there was an error with the speech recognition service.")
            return "Sorry, there was an error with the speech recognition service."

    def process(self, user_input):
        response = self.client.chat.completions.create(
            model=self.openai_model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_input},
            ],
        )
        return response.choices[0].message.content

    def speak(self, text):
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"

        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.elevenlabs_api_key,
        }

        data = {
            "text": " <break time='0.15s' /> " + text,
            "model_id": self.elevenlabs_model_id,
            "voice_settings": self.elevenlabs_voice_settings,
        }

        response = requests.post(url, json=data, headers=headers)

        if response.status_code == 200:
            audio = io.BytesIO(response.content)
            sound = AudioSegment.from_mp3(audio)
            pydub_play(sound)
        else:
            print(
                f"Error: Unable to generate speech. Status code: {response.status_code}"
            )
            print(f"Response content: {response.content}")
