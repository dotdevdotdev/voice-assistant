import openai
import speech_recognition as sr
import logging
import requests
import io
import os
from pydub import AudioSegment
from pydub.playback import play as pydub_play
from deepgram import (
    DeepgramClient,
    PrerecordedOptions,
    FileSource,
)


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

        # Initialize Deepgram client with API key from environment variable
        deepgram_api_key = os.environ.get("DEEPGRAM_API_KEY")
        if not deepgram_api_key:
            raise ValueError("DEEPGRAM_API_KEY environment variable is not set")
        self.deepgram = DeepgramClient(deepgram_api_key)

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

    async def listen(self):
        with sr.Microphone() as source:
            print("Listening...")
            audio = self.recognizer.listen(source)

        try:
            # Convert the audio to wav format
            wav_data = io.BytesIO()
            AudioSegment(data=audio.get_wav_data()).export(wav_data, format="wav")
            wav_data.seek(0)

            # Use Deepgram for transcription
            text = self.transcribe_with_deepgram(wav_data.read())
            return text
        except Exception as e:
            print(f"Error: {str(e)}")
            return "Sorry, there was an error with the speech recognition service."

    def transcribe_with_deepgram(self, audio_data):
        try:
            # Configure Deepgram options for audio analysis
            options = PrerecordedOptions(
                smart_format=True,
                model="nova-2",
                language="en-US",
            )

            # Prepare the audio payload
            payload: FileSource = {
                "buffer": audio_data,
            }

            # Call the transcribe_file method with the audio payload and options
            response = self.deepgram.listen.prerecorded.v("1").transcribe_file(
                payload, options
            )

            # Extract the transcript from the response
            transcript = response.results.channels[0].alternatives[0].transcript
            print(f"You said: {transcript}")
            return transcript
        except Exception as e:
            print(f"Error transcribing with Deepgram: {str(e)}")
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
