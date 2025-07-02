# Import Module
import logging
import time
import pyaudio
import threading
import sys
import os
import sounddevice as sd
import numpy as np
from queue import Queue
from pathlib import Path
from typing import Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add xiaozhi directory to Python path
xiaozhi_path = Path(__file__).parent / "xiaozhi"
if str(xiaozhi_path) not in sys.path:
    sys.path.insert(0, str(xiaozhi_path))

# Now import from xiaozhi
xiaozhi_main = None
try:
    # Change current directory to xiaozhi for imports to work
    original_cwd = os.getcwd()
    os.chdir(xiaozhi_path)
    
    from app import main as xiaozhi_main
    logger.info("✅ Successfully imported xiaozhi main function")
    
    # Restore original directory
    os.chdir(original_cwd)
    
except ImportError as e:
    logging.error(f"❌ Failed to import xiaozhi: {e}")
    xiaozhi_main = None
except Exception as e:
    logging.error(f"❌ Error setting up xiaozhi: {e}")
    xiaozhi_main = None
finally:
    # Make sure we restore directory even if there's an error
    try:
        os.chdir(original_cwd)
    except:
        pass

# Your other imports
from wake_word_detect import WakeWordDetector

class SimpleAudioStream:
    """Alternative audio stream using sounddevice."""
    
    def __init__(self, sample_rate=16000, chunk_size=960):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.queue = Queue()
        self.stream = None
        self._active = False
        
    def audio_callback(self, indata, frames, time, status):
        """Audio input callback."""
        if status:
            print(f"Audio callback status: {status}")
        # Convert float32 to int16
        audio_data = (indata[:, 0] * 32767).astype(np.int16).tobytes()
        self.queue.put(audio_data)
        
    def start_stream(self):
        """Start the audio stream."""
        try:
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype=np.float32,
                callback=self.audio_callback,
                blocksize=self.chunk_size
            )
            self.stream.start()
            self._active = True
            logger.info("SoundDevice audio stream started")
            return True
        except Exception as e:
            logger.error(f"Failed to start audio stream: {e}")
            return False
    
    def stop_stream(self):
        """Stop the audio stream."""
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
                self._active = False
                logger.info("Audio stream stopped")
            except Exception as e:
                logger.error(f"Error stopping stream: {e}")
    
    def is_active(self):
        """Check if stream is active."""
        return self._active and self.stream and self.stream.active
    
    def read(self, num_frames, exception_on_overflow=False):
        """Read audio data from queue."""
        try:
            if not self.queue.empty():
                return self.queue.get_nowait()
            return b''
        except:
            return b''
    
    def get_read_available(self):
        """Get number of frames available to read."""
        return self.queue.qsize() * self.chunk_size

class LunaWakeWordSystem:
    """LUNA Wake Word Detection System."""
    
    def __init__(self):
        self.detector = WakeWordDetector()
        self.audio_stream = SimpleAudioStream()
        self.running = False
        self.setup_callbacks()
    
    def setup_callbacks(self):
        """Setup wake word detection callbacks."""
        def on_wake_word_detected(wake_word, text):
            logger.info(f"🔥 Wake word detected: '{wake_word}' from text: '{text}'")
            self.handle_wake_word(wake_word, text)
        
        self.detector.on_detected(on_wake_word_detected)
    
    def handle_wake_word(self, wake_word, text):
        """Handle different wake words."""
        wake_word_lower = wake_word.lower()
        
        if wake_word_lower in ["露娜", "你好", "醒醒"]:
            logger.info("Wake word detected - Starting LUNA chat mode")
            self.start_chat_mode()
        else:
            logger.info(f"Unknown wake word: {wake_word}")
    
    def start_chat_mode(self):
        """Start chat mode without PyAudio conflicts."""
        try:
            # Stop current audio stream to avoid conflicts
            self.audio_stream.stop_stream()
            self.detector.pause()
            
            logger.info("Starting xiaozhi chat mode...")
            
            # Set environment variable to disable PyAudio in xiaozhi
            os.environ['DISABLE_PYAUDIO'] = '1'
            
            xiaozhi_main()
            
            logger.info("Chat ended, resuming wake word detection...")
            
            # Restart audio stream
            self.audio_stream.start_stream()
            self.detector.resume()
            
        except Exception as e:
            logger.error(f"Error in chat mode: {e}")
            # Ensure cleanup
            self.audio_stream.start_stream()
            self.detector.resume()
    
    def start(self):
        """Start the wake word detection system."""
        if not self.detector.enabled:
            logger.error("Wake word detector is not enabled")
            return False
        
        # Start audio stream
        if not self.audio_stream.start_stream():
            logger.error("Failed to start audio stream")
            return False
        
        # Start wake word detection
        if not self.detector.start(self.audio_stream):
            logger.error("Failed to start wake word detection")
            self.audio_stream.stop_stream()
            return False
        
        self.running = True
        logger.info("🎙️  LUNA Wake Word System started")
        return True
    
    def stop(self):
        """Stop the wake word detection system."""
        if self.running:
            self.running = False
            self.detector.stop()
            self.audio_stream.stop_stream()
            logger.info("LUNA Wake Word System stopped")
    
    def get_stats(self):
        """Get system statistics."""
        return self.detector.get_performance_stats()

def luna_awake():
    """Main LUNA wake word detection loop."""
    luna_system = LunaWakeWordSystem()
    
    try:
        # Start the wake word detection system
        if not luna_system.start():
            logger.error("Failed to start LUNA wake word system")
            return
        
        logger.info("LUNA is now listening for wake words...")
        logger.info("Press Ctrl+C to stop")
        
        # Keep the main thread alive
        while luna_system.running:
            time.sleep(1)
            
            # Optional: Print stats every 30 seconds
            # if int(time.time()) % 30 == 0:
            #     stats = luna_system.get_stats()
            #     logger.info(f"Stats: {stats}")
    
    except KeyboardInterrupt:
        logger.info("Detected User Keyboard Interrupt, shutting down...")
    
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    
    finally:
        luna_system.stop()
        logger.info("LUNA system shutdown complete")

if __name__ == "__main__":
    luna_awake()
