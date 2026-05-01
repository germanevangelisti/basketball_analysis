from ultralytics import YOLO
import supervision as sv
import numpy as np
import pandas as pd
import sys
sys.path.append('../')
from utils import read_stub, save_stub


class BallTracker:
    """Handles basketball detection using YOLO with filtering and interpolation."""

    def __init__(self, model_path):
        self.model = YOLO(model_path)

    def detect_frames(self, frames):
        batch_size = 20
        detections = []
        for i in range(0, len(frames), batch_size):
            detections_batch = self.model.predict(frames[i:i + batch_size], conf=0.5)
            detections += detections_batch
        return detections

    def detect_chunk(self, frames):
        """Detect ball in a chunk of frames. Returns list of per-frame track dicts."""
        detections = self.detect_frames(frames)
        chunk_tracks = []
        for detection in detections:
            cls_names_inv = {v: k for k, v in detection.names.items()}
            detection_sv = sv.Detections.from_ultralytics(detection)

            chosen_bbox = None
            max_confidence = 0
            for frame_det in detection_sv:
                bbox = frame_det[0].tolist()
                cls_id = frame_det[3]
                confidence = frame_det[2]
                if cls_id == cls_names_inv['Ball'] and confidence > max_confidence:
                    chosen_bbox = bbox
                    max_confidence = confidence

            frame_dict = {}
            if chosen_bbox is not None:
                frame_dict[1] = {"bbox": chosen_bbox}
            chunk_tracks.append(frame_dict)
        return chunk_tracks

    def get_object_tracks(self, frames, read_from_stub=False, stub_path=None):
        tracks = read_stub(read_from_stub, stub_path)
        if tracks is not None:
            if len(tracks) == len(frames):
                return tracks

        all_tracks = self.detect_chunk(frames)

        save_stub(stub_path, all_tracks)
        return all_tracks

    def remove_wrong_detections(self, ball_positions):
        maximum_allowed_distance = 25
        last_good_frame_index = -1

        for i in range(len(ball_positions)):
            current_box = ball_positions[i].get(1, {}).get('bbox', [])
            if len(current_box) == 0:
                continue
            if last_good_frame_index == -1:
                last_good_frame_index = i
                continue
            last_good_box = ball_positions[last_good_frame_index].get(1, {}).get('bbox', [])
            frame_gap = i - last_good_frame_index
            adjusted_max_distance = maximum_allowed_distance * frame_gap
            if np.linalg.norm(np.array(last_good_box[:2]) - np.array(current_box[:2])) > adjusted_max_distance:
                ball_positions[i] = {}
            else:
                last_good_frame_index = i

        return ball_positions

    def interpolate_ball_positions(self, ball_positions):
        ball_positions = [x.get(1, {}).get('bbox', []) for x in ball_positions]
        df_ball_positions = pd.DataFrame(ball_positions, columns=['x1', 'y1', 'x2', 'y2'])
        df_ball_positions = df_ball_positions.interpolate()
        df_ball_positions = df_ball_positions.bfill()
        ball_positions = [{1: {"bbox": x}} for x in df_ball_positions.to_numpy().tolist()]
        return ball_positions
