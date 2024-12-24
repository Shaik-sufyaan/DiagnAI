from dotenv import load_dotenv
import os
from google.cloud import texttospeech
from google.auth import credentials
import pygame
import io
load_dotenv()

def speak(text, speaker="en-US-Wavenet-C", emotion="neutral"):
    """
    Converts text to speech using Google Cloud TTS.

    Args:
        text: The text to be spoken.
        speaker: The voice of the speaker (default: "en-US-Wavenet-C").
        emotion: The desired emotion for the speech (default: "neutral").

    Raises:
        Exception: If an error occurs during the TTS process.
    """
    api_key = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    credentials = credentials.AnonymousCredentials() 
    client = texttospeech.TextToSpeechClient(credentials=credentials) 

    # Set up voice request
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name=speaker,  # Select the desired voice
    )

    # Set up audio config
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=1.0,  # Adjust speaking rate if needed
        pitch=0.0,  # Adjust pitch if needed
    )

    # Adjust voice based on emotion
    if emotion == "happy":
        audio_config.pitch += 0.2 
    elif emotion == "sad":
        audio_config.pitch -= 0.2
    elif emotion == "angry":
        audio_config.speaking_rate += 0.1

    # Synthesize speech
    synthesis_input = texttospeech.SynthesisInput(text=text)
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    # Play audio (using a library like pygame)
    pygame.mixer.init()
    pygame.mixer.music.load(io.BytesIO(response.audio_content))
    pygame.mixer.music.play()

    # Keep the script running until the audio finishes playing
    while pygame.mixer.music.get_busy():
        continue

if __name__ == "__main__":
    speak("Hello, how are you today?", speaker="en-US-Wavenet-D", emotion="happy")