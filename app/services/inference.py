import threading
import queue
import time
import cv2
import logging
import numpy as np
from app.core.config import settings

# Attempt to load DeepFace. If not installed properly, it will error out here.
try:
    from deepface import DeepFace
except ImportError:
    DeepFace = None
    logging.warning("DeepFace is not installed. Deep inference will be disabled.")

logger = logging.getLogger(__name__)

class DeepInferenceWorker:
    def __init__(self):
        self.queue = queue.Queue(maxsize=10) # Prevent memory overload if queue backs up
        self.cache = {} # face_id -> { "age": X, "gender": Y, "emotion": Z, "timestamp": T }
        self.cache_lock = threading.Lock()
        self.running = False
        self.thread = None

    def start(self):
        if not DeepFace:
            logger.error("Cannot start DeepInferenceWorker without DeepFace.")
            return

        self.running = True
        self.thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.thread.start()
        logger.info("DeepInferenceWorker started.")

    def stop(self):
        self.running = False
        if self.thread:
            # push a dummy item to wake up the queue if blocked
            try:
                self.queue.put_nowait(None)
            except queue.Full:
                pass
            self.thread.join(timeout=2.0)
            logger.info("DeepInferenceWorker stopped.")

    def enqueue_crop(self, face_id: int, crop: np.ndarray):
        if not self.running: return
        
        # Check if we recently cached this to avoid overwhelming queue
        with self.cache_lock:
            cached = self.cache.get(face_id)
            if cached and (time.time() - cached["timestamp"] < settings.CACHE_EXPIRATION_SEC):
                return
        
        try:
            self.queue.put_nowait((face_id, crop))
        except queue.Full:
            pass # Skip frame if queue is full

    def get_cached_attributes(self, face_id: int):
        with self.cache_lock:
            return self.cache.get(face_id)

    def _worker_loop(self):
        # Pre-load models to avoid lag on first frame
        try:
            # We run a dummy analyze to force deepface to download/load weights into memory
            dummy_img = np.zeros((224, 224, 3), dtype=np.uint8)
            DeepFace.analyze(dummy_img, actions=settings.DEEPFACE_MODELS, enforce_detection=False, silent=True)
            logger.info("DeepFace models loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load DeepFace models: {e}")

        while self.running:
            try:
                item = self.queue.get(timeout=1.0)
                if item is None: continue # Shutdown signal
                
                face_id, crop = item
                
                # Double check we didn't just update it from another queued item
                with self.cache_lock:
                    cached = self.cache.get(face_id)
                    if cached and (time.time() - cached["timestamp"] < settings.CACHE_EXPIRATION_SEC):
                        self.queue.task_done()
                        continue

                # Run inference
                try:
                    # Convert BGR to RGB for DeepFace
                    rgb_crop = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
                    results = DeepFace.analyze(
                        img_path=rgb_crop,
                        actions=settings.DEEPFACE_MODELS,
                        enforce_detection=False,
                        silent=True
                    )
                    
                    if isinstance(results, list):
                        res = results[0]
                    else:
                        res = results
                        
                    age = res.get('age')
                    emotion = res.get('dominant_emotion')
                    
                    # Gender comes as a dict, get the dominant one
                    gender_dict = res.get('gender', {})
                    if isinstance(gender_dict, dict):
                        gender = max(gender_dict, key=gender_dict.get) if gender_dict else None
                    else:
                        gender = gender_dict

                    with self.cache_lock:
                        self.cache[face_id] = {
                            "age": age,
                            "gender": gender,
                            "emotion": emotion,
                            "timestamp": time.time()
                        }
                except Exception as e:
                    logger.debug(f"DeepFace inference failed on crop: {e}")
                
                self.queue.task_done()
            except queue.Empty:
                pass

# Global worker instance
deep_worker = DeepInferenceWorker()
