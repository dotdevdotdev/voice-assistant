import speech_recognition as sr
import logging
from deepgram import DeepgramClient
import asyncio
import os
import io


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def transcribe_audio(audio_data):
    """
    Transcribe audio using Deepgram
    """
    try:
        # Initialize Deepgram client
        deepgram = DeepgramClient(os.getenv("DEEPGRAM_API_KEY"))

        # Get the raw WAV data as bytes
        wav_data = audio_data.get_wav_data()

        # Create a BytesIO object
        buffer = io.BytesIO(wav_data)

        # Use the current Deepgram API with the buffer
        response = await deepgram.listen.prerecorded.v("1").transcribe(
            buffer,
            {
                "smart_format": True,
                "model": "nova",
                "language": "en",
                "mimetype": "audio/wav",
            },
        )

        # Extract transcription from the response
        transcript = response["results"]["channels"][0]["alternatives"][0]["transcript"]

        return transcript

    except Exception as e:
        logger.error(f"Error in transcribe_audio: {str(e)}")
        raise


# Function to be called from your main loop
def transcribe_speech(audio_data):
    return asyncio.run(transcribe_audio(audio_data))


# ... (rest of the file)
