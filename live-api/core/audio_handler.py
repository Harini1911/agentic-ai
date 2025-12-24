"""
Audio handler for real-time audio streaming.

Manages microphone input capture and speaker output playback
with proper buffering and interruption handling.
"""

import asyncio
from typing import Optional
import pyaudio


class AudioHandler:
    """
    Handles real-time audio input/output for Live API.
    
    Features:
    - Microphone input capture (16kHz PCM)
    - Speaker output playback (24kHz PCM)
    - Async queue-based buffering
    - Interruption (barge-in) support
    """
    
    # Audio configuration constants
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    INPUT_SAMPLE_RATE = 16000  # Gemini expects 16kHz input
    OUTPUT_SAMPLE_RATE = 24000  # Gemini outputs 24kHz
    CHUNK_SIZE = 1024
    
    def __init__(self):
        """Initialize audio handler."""
        self.pya = pyaudio.PyAudio()
        self.input_stream: Optional[pyaudio.Stream] = None
        self.output_stream: Optional[pyaudio.Stream] = None
        
        # Async queues for audio data
        self.input_queue = asyncio.Queue(maxsize=5)
        self.output_queue = asyncio.Queue()
        
        self._listening = False
        self._playing = False
    
    async def start_listening(self):
        """Start capturing audio from microphone."""
        if self._listening:
            return
        
        try:
            mic_info = self.pya.get_default_input_device_info()
            
            self.input_stream = await asyncio.to_thread(
                self.pya.open,
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.INPUT_SAMPLE_RATE,
                input=True,
                input_device_index=mic_info["index"],
                frames_per_buffer=self.CHUNK_SIZE,
            )
            
            self._listening = True
            print("🎤 Microphone started")
            
        except Exception as e:
            print(f"❌ Failed to start microphone: {e}")
            raise
    
    async def stop_listening(self):
        """Stop capturing audio from microphone."""
        self._listening = False
        
        if self.input_stream:
            await asyncio.to_thread(self.input_stream.stop_stream)
            await asyncio.to_thread(self.input_stream.close)
            self.input_stream = None
            print("🎤 Microphone stopped")
    
    async def start_playback(self):
        """Start audio playback to speakers."""
        if self._playing:
            return
        
        try:
            self.output_stream = await asyncio.to_thread(
                self.pya.open,
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.OUTPUT_SAMPLE_RATE,
                output=True,
            )
            
            self._playing = True
            print("🔊 Speaker started")
            
        except Exception as e:
            print(f"❌ Failed to start speaker: {e}")
            raise
    
    async def stop_playback(self):
        """Stop audio playback."""
        self._playing = False
        
        if self.output_stream:
            await asyncio.to_thread(self.output_stream.stop_stream)
            await asyncio.to_thread(self.output_stream.close)
            self.output_stream = None
            print("🔊 Speaker stopped")
    
    async def capture_audio_loop(self):
        """
        Continuously capture audio from microphone and put in queue.
        
        This should run as a background task.
        """
        kwargs = {"exception_on_overflow": False} if __debug__ else {}
        
        while self._listening and self.input_stream:
            try:
                data = await asyncio.to_thread(
                    self.input_stream.read,
                    self.CHUNK_SIZE,
                    **kwargs
                )
                
                # Put in queue (non-blocking, drop if full)
                try:
                    self.input_queue.put_nowait({
                        "data": data,
                        "mime_type": "audio/pcm"
                    })
                except asyncio.QueueFull:
                    # Drop oldest frame if queue is full
                    try:
                        self.input_queue.get_nowait()
                        self.input_queue.put_nowait({
                            "data": data,
                            "mime_type": "audio/pcm"
                        })
                    except:
                        pass
                        
            except Exception as e:
                print(f"⚠️  Audio capture error: {e}")
                await asyncio.sleep(0.1)
    
    async def playback_audio_loop(self):
        """
        Continuously play audio from queue to speakers.
        
        This should run as a background task.
        """
        while self._playing and self.output_stream:
            try:
                # Get audio data from queue
                audio_data = await self.output_queue.get()
                
                # Play audio
                await asyncio.to_thread(
                    self.output_stream.write,
                    audio_data
                )
                
            except Exception as e:
                print(f"⚠️  Audio playback error: {e}")
                await asyncio.sleep(0.1)
    
    async def get_input_audio(self) -> dict:
        """
        Get next audio chunk from input queue.
        
        Returns:
            Dict with 'data' and 'mime_type' keys
        """
        return await self.input_queue.get()
    
    async def queue_output_audio(self, audio_data: bytes):
        """
        Queue audio data for playback.
        
        Args:
            audio_data: Raw audio bytes to play
        """
        await self.output_queue.put(audio_data)
    
    def clear_output_queue(self):
        """
        Clear output queue (for handling interruptions).
        
        This stops playback of queued audio immediately.
        """
        while not self.output_queue.empty():
            try:
                self.output_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
    
    async def cleanup(self):
        """Clean up audio resources."""
        await self.stop_listening()
        await self.stop_playback()
        
        # Clear queues
        while not self.input_queue.empty():
            try:
                self.input_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        
        self.clear_output_queue()
        
        # Terminate PyAudio
        self.pya.terminate()
        print("🔇 Audio handler cleaned up")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_listening()
        await self.start_playback()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
