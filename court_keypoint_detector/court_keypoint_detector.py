from ultralytics import YOLO
import sys
sys.path.append('../')
from utils import read_stub, save_stub


class CourtKeypointDetector:
    """Uses a YOLO keypoint model to detect 18 court landmarks per frame."""

    def __init__(self, model_path):
        self.model = YOLO(model_path)

    def detect_chunk(self, frames):
        """Detect court keypoints in a chunk of frames."""
        batch_size = 20
        keypoints = []
        for i in range(0, len(frames), batch_size):
            batch_results = self.model.predict(frames[i:i + batch_size], conf=0.5)
            for detection in batch_results:
                keypoints.append(detection.keypoints)
        return keypoints

    def get_court_keypoints(self, frames, read_from_stub=False, stub_path=None):
        court_keypoints = read_stub(read_from_stub, stub_path)
        if court_keypoints is not None:
            if len(court_keypoints) == len(frames):
                return court_keypoints

        court_keypoints = self.detect_chunk(frames)

        save_stub(stub_path, court_keypoints)
        return court_keypoints
