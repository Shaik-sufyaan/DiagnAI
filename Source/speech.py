import torch
from transformers import pipeline
from gtts import gTTS
import sounddevice as sd
import numpy as np
import threading
import queue
from typing import Optional, List, Tuple
import time
import io
from pydub import AudioSegment
from pydub.playback import play
import pyaudio
import tempfile
import os


from google.cloud import texttospeech


class VoiceManager:
    """Manages available voices and voice selection for gTTS"""
    def __init__(self):
        self.available_voices = {
            'en-us': 'English (US)',
            'en-uk': 'English (UK)',
            'en-au': 'English (Australia)',
            'en-in': 'English (India)'
        }
        self.current_voice = 'en-us'
        
    def list_voices(self) -> dict:
        """Returns dictionary of available voices"""
        return self.available_voices
    
    def set_voice(self, voice_id: str) -> bool:
        """Set current voice"""
        if voice_id in self.available_voices:
            self.current_voice = voice_id
            return True
        return False

class SpeechRecognizer:
    """Handles speech recognition with emotion/tonality detection"""
    def __init__(self):
        # Using Whisper model with GPU if available
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {device}")
        
        self.asr_pipeline = pipeline("automatic-speech-recognition", 
                                   model="openai/whisper-base",
                                   device=device)
        
        self.emotion_detector = pipeline("audio-classification",
                                       model="ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition",
                                       device=device)
    
    def record_audio(self, duration: int = 5) -> np.ndarray:
        """Record audio for specified duration"""
        sample_rate = 16000
        print("Recording...")
        recording = sd.rec(int(duration * sample_rate), 
                         samplerate=sample_rate, 
                         channels=1,  # Explicitly set to mono
                         dtype=np.float32)  # Set correct dtype
        sd.wait()
        print("Recording finished!")
        return recording.squeeze()  # Remove extra dimension to ensure 1D array
    
    def analyze_speech(self, audio_data: np.ndarray) -> Tuple[str, dict]:
        """
        Analyze speech to extract text and emotional content
        Returns: (transcribed_text, emotion_data)
        """
        try:
            # Ensure audio is properly formatted (mono, float32, correct shape)
            if len(audio_data.shape) > 1:
                audio_data = audio_data.mean(axis=1)  # Convert to mono if stereo
            
            # Normalize audio
            audio_data = audio_data / np.max(np.abs(audio_data))
            
            # Transcribe audio
            transcription = self.asr_pipeline({"sampling_rate": 16000, "raw": audio_data})["text"]
            
            # Detect emotion/tonality
            emotion_result = self.emotion_detector(audio_data)
            emotion_data = {
                "primary_emotion": emotion_result[0]["label"],
                "confidence": emotion_result[0]["score"],
                "secondary_emotions": [
                    (result["label"], result["score"]) 
                    for result in emotion_result[1:]
                ]
            }
            
            return transcription, emotion_data
            
        except Exception as e:
            print(f"Error in speech analysis: {str(e)}")
            print(f"Audio data shape: {audio_data.shape}")
            print(f"Audio data type: {audio_data.dtype}")
            raise

class SpeechSynthesizer:
    """Handles text-to-speech with live synthesis using gTTS"""
    def __init__(self, voice_manager: VoiceManager):
        self.voice_manager = voice_manager
        self.audio_queue = queue.Queue()
        self.is_speaking = False
        
    def synthesize_text(self, 
                       text: str, 
                       slow: bool = False) -> AudioSegment:
        """Convert text to speech using gTTS"""
        if not text.strip():
            return None
            
        # Create gTTS object
        tts = gTTS(text=text, 
                   lang=self.voice_manager.current_voice[:2],
                   tld=self.voice_manager.current_voice[3:] if '-' in self.voice_manager.current_voice else None,
                   slow=slow)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
            tts.save(fp.name)
            audio = AudioSegment.from_mp3(fp.name)
            os.unlink(fp.name)
        
        return audio
    
    def start_live_synthesis(self):
        """Start background thread for live synthesis"""
        self.is_speaking = True
        threading.Thread(target=self._speak_from_queue, daemon=True).start()
        
    def stop_live_synthesis(self):
        """Stop live synthesis"""
        self.is_speaking = False
        
    def _speak_from_queue(self):
        """Background process for live synthesis"""
        current_text = ""
        while self.is_speaking:
            try:
                char = self.audio_queue.get_nowait()
                current_text += char
                
                # Synthesize when we have a word or punctuation
                if char in " .,!?":
                    audio = self.synthesize_text(current_text.strip(), 
                                               slow=current_text.isupper())
                    if audio:
                        play(audio)
                    current_text = ""
                    
            except queue.Empty:
                if current_text.strip():  # Speak any remaining text
                    audio = self.synthesize_text(current_text.strip())
                    if audio:
                        play(audio)
                    current_text = ""
                time.sleep(0.1)
                
    def add_live_text(self, text: str):
        """Add text to live synthesis queue"""
        self.audio_queue.put(text)

    def google_tts_play(self, text):
        """Synthesizes speech from the input string of text and plays it directly."""

        client = texttospeech.TextToSpeechClient()

        input_text = texttospeech.SynthesisInput(text=text)

        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US", ssml_gender=texttospeech.enums.SsmlVoiceGender.NEUTRAL
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.enums.AudioEncoding.LINEAR16
        )

        response = client.synthesize_speech(input_text=input_text, voice=voice, audio_config=audio_config)

        # Initialize PyAudio
        p = pyaudio.PyAudio()

        # Define stream parameters
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=24000, output=True) 

        # Play the audio
        stream.write(response.audio_content)

        # Close the stream and PyAudio
        stream.stop_stream()
        stream.close()
        p.terminate()

        print("Audio played.")



def main():
    # Initialize components
    voice_manager = VoiceManager()
    recognizer = SpeechRecognizer()
    synthesizer = SpeechSynthesizer(voice_manager)
    
    # List available voices
    print("Available voices:", voice_manager.list_voices())
    
    # Set voice
    voice_manager.set_voice("en-us")
    
    # Record and analyze speech
    print("Recording 5 seconds of speech...")
    audio = recognizer.record_audio(5)
    text, emotion = recognizer.analyze_speech(audio)
    print(f"Transcribed text: {text}")
    print(f"Detected emotion: {emotion}")
    
    # Synthesize response
    response = "I understood what you said!"
    audio = synthesizer.synthesize_text(response)
    if audio:
        play(audio)
    
    # Demo live synthesis
    print("Starting live synthesis...")
    synthesizer.start_live_synthesis()
    
    # Simulate typing
    test_text = "This is a test of live synthesis!"
    for char in test_text:
        synthesizer.add_live_text(char)
        time.sleep(0.1)
    
    time.sleep(2)  # Wait for final synthesis to complete
    synthesizer.stop_live_synthesis()

    # Example usage
    text_to_speak = "Hello, this is a sample text for Google Cloud Text-to-Speech."
    synthesizer.synthesize_text(text_to_speak)

if __name__ == "__main__":
    main()