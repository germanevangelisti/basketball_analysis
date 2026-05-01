from ultralytics import YOLO
import supervision as sv
import sys
sys.path.append('../')
from utils import read_stub, save_stub


class PlayerTracker:
    """
    Handles player detection and tracking using YOLO and ByteTrack.

    Supports two usage modes:
    - Streaming: call track_chunk() repeatedly; ByteTrack state persists between calls
      so player IDs stay consistent across the full video without loading all frames.
    - Legacy: call get_object_tracks() with a full frame list (resets tracker state).
    """

    def __init__(self, model_path):
        self.model = YOLO(model_path)
        self.tracker = sv.ByteTrack()

    def detect_frames(self, frames):
        batch_size = 20
        detections = []
        for i in range(0, len(frames), batch_size):
            detections_batch = self.model.predict(frames[i:i + batch_size], conf=0.5)
            detections += detections_batch
        return detections

    def track_chunk(self, frames):
        """Process a chunk of frames, return per-frame track dicts.

        ByteTrack state (self.tracker) persists between calls so player IDs remain
        consistent when this is called repeatedly while streaming a video.
        """
        detections = self.detect_frames(frames)
        chunk_tracks = []
        for detection in detections:
            cls_names_inv = {v: k for k, v in detection.names.items()}
            detection_sv = sv.Detections.from_ultralytics(detection)
            detection_with_tracks = self.tracker.update_with_detections(detection_sv)

            frame_dict = {}
            for frame_detection in detection_with_tracks:
                bbox = frame_detection[0].tolist()
                cls_id = frame_detection[3]
                track_id = frame_detection[4]
                if cls_id == cls_names_inv['Player']:
                    frame_dict[track_id] = {"bbox": bbox}
            chunk_tracks.append(frame_dict)
        return chunk_tracks

    def get_object_tracks(self, frames, read_from_stub=False, stub_path=None):
        tracks = read_stub(read_from_stub, stub_path)
        if tracks is not None:
            if len(tracks) == len(frames):
                return tracks

        # Reset tracker for fresh full-video processing
        self.tracker = sv.ByteTrack()
        all_tracks = self.track_chunk(frames)

        save_stub(stub_path, all_tracks)
        return all_tracks
