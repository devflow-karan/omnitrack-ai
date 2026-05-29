import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import audio
from mediapipe.tasks.python.components import containers
import logging
import time

logger = logging.getLogger(__name__)

# Subset of YAMNet categories that represent animals/birds.
TARGET_CATEGORIES = {
    "Dog", "Bark", "Howl", "Bow-wow", "Growling", "Whimper (dog)", 
    "Cat", "Purr", "Meow", "Hiss", "Caterwaul", "Horse", 
    "Neigh, whinny", "Snort", "Donkey, ass", "Mule", "Cow", "Bovinae", "Moo", "Pig", "Oink", "Rooster", 
    "Cluck", "Crowing, cock-a-doodle-doo", "Chicken", "Piglet, squeal", "Sheep", "Goat", "Bleat",
    "Bird", "Bird vocalization, bird call, bird song", "Chirp, tweet", "Squawk", "Pigeon, dove", "Coo",
    "Crow", "Caw", "Owl", "Hoot", "Bird flight, flapping wings", "Roaring cats (lions, tigers)", 
    "Roar", "Bird of prey", "Frog", "Croak", "Snake", "Rattle", "Cricket", "Mosquito", "Fly, housefly", "Buzz"
}

class YAMNetAudioClassifier:
    def __init__(self, buffer_size=15600):
        # YAMNet requires chunks of 15600 samples (0.975 sec at 16kHz)
        self.buffer_size = buffer_size
        self.audio_buffer = np.array([], dtype=np.float32)
        
        base_options = python.BaseOptions(model_asset_path='app/models/yamnet.tflite')
        options = audio.AudioClassifierOptions(
            base_options=base_options, 
            max_results=3,
            score_threshold=0.3
        )
        self.classifier = audio.AudioClassifier.create_from_options(options)
        self.audio_format = containers.AudioDataFormat(1, 16000)

        # To prevent Jarvis from talking continuously, we keep track of the last time we emitted an event
        self.last_event_time = 0
        self.cooldown_sec = 4.0

    def process(self, float_array: np.ndarray) -> str | None:
        """
        Takes raw 16kHz PCM audio floats, buffers them, and runs classification when enough data is collected.
        Returns the name of the animal/bird if detected, else None.
        """
        self.audio_buffer = np.concatenate((self.audio_buffer, float_array))
        
        detected_event = None
        
        # We can process multiple chunks if we received a lot of data
        while len(self.audio_buffer) >= self.buffer_size:
            chunk = self.audio_buffer[:self.buffer_size]
            self.audio_buffer = self.audio_buffer[self.buffer_size:]
            
            # Rate limit speaking
            if time.time() - self.last_event_time < self.cooldown_sec:
                continue

            try:
                audio_data = containers.AudioData.create_from_array(chunk, 16000.0)
                results = self.classifier.classify(audio_data)
                
                for result in results:
                    if result.classifications:
                        for classification in result.classifications:
                            for category in classification.categories:
                                if category.category_name in TARGET_CATEGORIES:
                                    detected_event = category.category_name
                                    self.last_event_time = time.time()
                                    logger.info(f"Audio Event Detected: {detected_event} ({category.score})")
                                    break
                            if detected_event:
                                break
                    if detected_event:
                        break
            except Exception as e:
                logger.error(f"Audio classification error: {e}")
                
        return detected_event

    def close(self):
        self.classifier.close()
