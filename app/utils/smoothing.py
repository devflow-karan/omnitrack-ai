class TemporalSmoother:
    def __init__(self, alpha: float = 0.2):
        """
        Initializes the TemporalSmoother for numerical values (e.g., Age).
        alpha: Smoothing factor (0.0 < alpha <= 1.0). Lower = more smoothing.
        """
        self.alpha = alpha
        self.value = None

    def update(self, new_value: float) -> float:
        if self.value is None:
            self.value = new_value
        else:
            self.value = self.alpha * new_value + (1 - self.alpha) * self.value
        return self.value

class EmotionSmoother:
    def __init__(self, history_size: int = 5):
        """
        Initializes the EmotionSmoother which returns the most frequent emotion
        over the last `history_size` updates.
        """
        self.history_size = history_size
        self.history = []

    def update(self, new_emotion: str) -> str:
        self.history.append(new_emotion)
        if len(self.history) > self.history_size:
            self.history.pop(0)
        
        # Return most frequent
        return max(set(self.history), key=self.history.count)
