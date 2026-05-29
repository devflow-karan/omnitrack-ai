import time

class FPSCounter:
    def __init__(self, alpha: float = 0.9):
        """
        Initializes the FPS Counter.
        :param alpha: Smoothing factor for exponential moving average (EMA) between 0 and 1.
        """
        self.alpha = alpha
        self.fps = 0.0
        self.prev_time = 0.0
        self.frame_count = 0

    def start(self) -> None:
        self.prev_time = time.perf_counter()
        self.fps = 0.0
        self.frame_count = 0

    def update(self) -> float:
        self.frame_count += 1
        current_time = time.perf_counter()
        elapsed = current_time - self.prev_time
        self.prev_time = current_time

        if elapsed > 0:
            instantaneous_fps = 1.0 / elapsed
            if self.fps == 0.0:
                self.fps = instantaneous_fps
            else:
                # Exponential Moving Average (EMA) smoothing
                self.fps = (self.alpha * self.fps) + ((1.0 - self.alpha) * instantaneous_fps)
        return self.fps

    @property
    def current_fps(self) -> float:
        return round(self.fps, 1)
