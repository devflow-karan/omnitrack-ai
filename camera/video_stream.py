import cv2
import threading
import time
import logging
from typing import Union, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ThreadedVideoStream:
    def __init__(
        self, 
        source: Union[int, str] = 0, 
        width: int = 640, 
        height: int = 480, 
        fps: int = 30
    ) -> None:
        """
        Multi-threaded camera stream reader to prevent main pipeline blocking.
        :param source: Webcam device index or RTSP stream URL.
        :param width: Target camera width.
        :param height: Target camera height.
        :param fps: Target capture FPS.
        """
        self.source = source
        self.width = width
        self.height = height
        self.fps = fps

        self.cap: Optional[cv2.VideoCapture] = None
        self.frame = None
        self.is_running = False
        self.is_connected = False
        
        self.thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()

    def start(self) -> "ThreadedVideoStream":
        """
        Start the background capture thread.
        """
        if self.is_running:
            return self
        
        self.is_running = True
        self.thread = threading.Thread(target=self._update_loop, name="CameraGrabberThread", daemon=True)
        self.thread.start()
        return self

    def _connect(self) -> bool:
        """
        Try to initialize the cv2.VideoCapture object.
        """
        try:
            logger.info(f"Connecting to video source: {self.source}")
            self.cap = cv2.VideoCapture(self.source)
            
            # Set properties if it's a hardware webcam (integer source)
            if isinstance(self.source, int):
                # Using DirectShow back-end on Windows, or default on Linux
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            
            if not self.cap.isOpened():
                logger.error(f"Failed to open video source: {self.source}")
                self.is_connected = False
                return False
            
            self.is_connected = True
            logger.info(f"Successfully connected to video source: {self.source}")
            return True
        except Exception as e:
            logger.error(f"Error connecting to video source: {e}")
            self.is_connected = False
            return False

    def _update_loop(self) -> None:
        """
        Background loop to continuously read frames.
        """
        retry_delay = 2.0  # seconds

        while self.is_running:
            if not self.is_connected or self.cap is None or not self.cap.isOpened():
                if not self._connect():
                    time.sleep(retry_delay)
                    continue

            grabbed, frame = self.cap.read()

            if not grabbed:
                logger.warning("Frame grab failed. Disconnecting for reconnection retry...")
                self.is_connected = False
                if self.cap:
                    self.cap.release()
                time.sleep(0.5)
                continue

            with self.lock:
                self.frame = frame

            # Control frame rate slightly so we don't spin-lock the CPU if camera reads instantly
            time.sleep(1.0 / (self.fps * 2.0))

    def read(self):
        """
        Read the latest grabbed frame. Returns None if no frame is available yet.
        """
        with self.lock:
            return self.frame.copy() if self.frame is not None else None

    def stop(self) -> None:
        """
        Stop the thread and release resources.
        """
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            
        with self.lock:
            if self.cap:
                self.cap.release()
                self.cap = None
            self.is_connected = False
            self.frame = None
        logger.info("Video stream stopped.")
