import speech_recognition as sr
from deepgram import Deepgram
import asyncio
import os


async def transcribe_audio(audio_data):
    try:
        # Attempt to transcribe with Deepgram
        dg_client = Deepgram(os.getenv("DEEPGRAM_API_KEY"))

        # Convert AudioData to bytes
        audio_bytes = audio_data.get_raw_data()

        source = {"buffer": audio_bytes, "mimetype": "audio/raw"}
        response = await dg_client.transcription.prerecorded(
            source,
            {
                "punctuate": True,
                "encoding": "linear16",
                "sample_rate": audio_data.sample_rate,
            },
        )
        return response["results"]["channels"][0]["alternatives"][0]["transcript"]
    except Exception as e:
        print(f"Error transcribing with Deepgram: {str(e)}")

        # Fallback to Google Speech Recognition
        recognizer = sr.Recognizer()
        try:
            return recognizer.recognize_google(audio_data)
        except sr.UnknownValueError:
            return "Google Speech Recognition could not understand audio"
        except sr.RequestError as e:
            return (
                f"Could not request results from Google Speech Recognition service; {e}"
            )


# Function to be called from your main loop
def transcribe_speech(audio_data):
    return asyncio.run(transcribe_audio(audio_data))


# ... (rest of the file)
