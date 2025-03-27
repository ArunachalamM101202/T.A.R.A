# modules/voice_processor.py

import os
import streamlit as st
from io import BytesIO
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs

class VoiceProcessor:
    """Class to handle text-to-speech conversion using Eleven Labs."""
    
    def __init__(self):
        """Initialize the voice processor with Eleven Labs API."""
        # Check if API key is set
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if api_key:
            self.client = ElevenLabs(api_key=api_key)
            self.is_available = True
        else:
            self.client = None
            self.is_available = False
            
        # Default voice settings
        self.voice_id = "pNInz6obpgDQGcFmaJgB"  # Adam voice
        self.model_id = "eleven_multilingual_v2"
        self.voice_settings = VoiceSettings(
            stability=0.0,
            similarity_boost=1.0,
            style=0.0,
            use_speaker_boost=True,
        )
    
    def text_to_speech(self, text):
        """
        Convert text to speech using Eleven Labs API.
        
        Args:
            text: Text to convert to speech
            
        Returns:
            BytesIO object containing the audio data, or None if conversion failed
        """
        if not self.is_available or not self.client:
            return None
            
        try:
            # Limit text length if needed (Eleven Labs has character limits)
            if len(text) > 5000:  # adjust based on your API tier
                text = text[:5000] + "..."
                
            # Perform the text-to-speech conversion
            response = self.client.text_to_speech.convert(
                voice_id=self.voice_id,
                output_format="mp3_22050_32",
                text=text,
                model_id=self.model_id,
                voice_settings=self.voice_settings,
            )
            
            # Create a BytesIO object to hold the audio data
            audio_stream = BytesIO()
            
            # Write each chunk of audio data to the stream
            for chunk in response:
                if chunk:
                    audio_stream.write(chunk)
                    
            # Reset stream position to the beginning
            audio_stream.seek(0)
            
            return audio_stream
            
        except Exception as e:
            st.error(f"Error converting text to speech: {str(e)}")
            return None