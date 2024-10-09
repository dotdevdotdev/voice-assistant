import speech_recognition as sr
import openai
from openai import OpenAI
import requests
import json
import io
from pydub import AudioSegment
from pydub.playback import play as pydub_play
import logging

NORMAL_ASSISTANT_MODEL = "gpt-4o-mini"
NORMAL_ASSISTANT_SYSTEM_PROMPT = """
You speak in short sentences. Only enough words to answer the question or convery the information needed. Speak in a very natural way as if you are a human. Ask short questions if needed to get the information you need. Do not use words like 'certainly', or 'definitely'. Use casual short words as much as possible without being too verbose. Speak in a very conversational tone. You should be clever and witty. If there's a pun or a funny way to phrase a response, you should use that one. Deliver it well with good intonation and tone. Use commas and periods as breaks. Do not use emojis or hastags or any other special characters. Begin responses with '...' and then either 'well' or 'hmm' or 'ya know' or 'I mean' or 'supposin' or 'coulda' or 'but' or 'couldn't' or 'hey'
"""

REALTIME_ASSISTANT_SYSTEM_PROMPT = NORMAL_ASSISTANT_SYSTEM_PROMPT
REALTIME_ASSISTANT_MODEL = NORMAL_ASSISTANT_MODEL

ELEVENLABS_MODEL_ID = "eleven_turbo_v2_5"
ELEVENLABS_VOICE_SETTINGS = {"stability": 0.5, "similarity_boost": 0.5}


class Assistant:
    def __init__(
        self, openai_api_key, elevenlabs_api_key, voice_id, realtime_mode=False
    ):
        self.recognizer = sr.Recognizer()
        openai.api_key = openai_api_key
        self.client = OpenAI()
        self.elevenlabs_api_key = elevenlabs_api_key
        self.voice_id = voice_id
        self.realtime_mode = realtime_mode
        self.device_found = False

        # Configure logging
        logging.basicConfig(level=logging.WARNING)
        logging.getLogger("speech_recognition").setLevel(logging.ERROR)

    def listen(self):
        with sr.Microphone() as source:
            if not self.device_found:
                print("Listening...")
                self.device_found = True
                logging.info(f"Connected to microphone: {source.device_index}")
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
            model=REALTIME_ASSISTANT_MODEL,
            messages=[
                {"role": "system", "content": REALTIME_ASSISTANT_SYSTEM_PROMPT},
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
            "text": text,
            "model_id": ELEVENLABS_MODEL_ID,
            "voice_settings": ELEVENLABS_VOICE_SETTINGS,
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

    def process_message(self, message):
        if self.realtime_mode:
            return self.process_realtime(message)
        else:
            return self.process_normal(message)

    def process_normal(self, message):
        response = openai.ChatCompletion.create(
            model=NORMAL_ASSISTANT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": NORMAL_ASSISTANT_SYSTEM_PROMPT,
                },
                {"role": "user", "content": message},
            ],
        )
        return response.choices[0].message["content"]

    def process_realtime(self, message):
        response = ""
        for chunk in openai.ChatCompletion.create(
            model=REALTIME_ASSISTANT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": REALTIME_ASSISTANT_SYSTEM_PROMPT,
                },
                {"role": "user", "content": message},
            ],
            stream=True,
        ):
            if chunk.choices[0].delta.get("content"):
                response += chunk.choices[0].delta.content
        return response
