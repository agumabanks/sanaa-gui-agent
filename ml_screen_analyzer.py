"""Machine-learning helpers for screen activity insights."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import numpy as np

try:  # Optional heavy dependency loaded lazily by installer
    from sklearn.cluster import KMeans
except ImportError as exc:  # pragma: no cover - instructor guidance will surface during runtime
    raise ImportError(
        "scikit-learn is required for ScreenActivityClassifier. Install it with: pip install scikit-learn"
    ) from exc


try:
    import pyautogui
except ImportError as exc:  # pragma: no cover - pyautogui already required elsewhere
    raise ImportError(
        "pyautogui is required for capturing screen frames. Install it with: pip install pyautogui"
    ) from exc


@dataclass
class ScreenActivitySummary:
    """Aggregated analytics about the current screen."""

    dominant_colors: List[Tuple[int, int, int]]
    brightness_score: float
    saturation_score: float

    def label(self) -> str:
        """Return a coarse label describing the screen state."""
        if self.brightness_score < 40:
            return "dark"
        if self.brightness_score > 200:
            return "bright"
        if self.saturation_score < 30:
            return "low_saturation"
        return "balanced"


class ScreenActivityClassifier:
    """Simple KMeans-based classifier for screen activity snapshots."""

    def __init__(self, sample_size: int = 5000, clusters: int = 4, random_state: int = 42):
        self.sample_size = sample_size
        self.clusters = clusters
        self.random_state = random_state

    def capture_pixels(self) -> np.ndarray:
        """Capture a screenshot and return a sampled RGB array."""
        screenshot = pyautogui.screenshot()
        pixels = np.array(screenshot)
        height, width, _ = pixels.shape
        flattened = pixels.reshape(-1, 3)

        if len(flattened) <= self.sample_size:
            return flattened

        indices = np.random.choice(flattened.shape[0], self.sample_size, replace=False)
        return flattened[indices]

    def analyze(self) -> ScreenActivitySummary:
        """Run unsupervised clustering to determine dominant colors and heuristics."""
        sample = self.capture_pixels().astype(float)
        kmeans = KMeans(n_clusters=self.clusters, n_init=10, random_state=self.random_state)
        kmeans.fit(sample)

        centers = kmeans.cluster_centers_.clip(0, 255).astype(int)
        dominant_colors = [tuple(map(int, center)) for center in centers]

        brightness = float(np.mean(sample[:, :3].mean(axis=1)))
        saturation = float(np.mean(sample.std(axis=1)))

        return ScreenActivitySummary(
            dominant_colors=dominant_colors,
            brightness_score=brightness,
            saturation_score=saturation,
        )
