import cv2
import os


def read_video(video_path):
    cap = cv2.VideoCapture(video_path)
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    return frames


def save_video(output_video_frames, output_video_path):
    output_dir = os.path.dirname(output_video_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(output_video_path, fourcc, 24,
                          (output_video_frames[0].shape[1], output_video_frames[0].shape[0]))
    for frame in output_video_frames:
        out.write(frame)
    out.release()


class VideoReader:
    """Streams a video file in fixed-size chunks to avoid loading all frames into RAM."""

    def __init__(self, video_path, chunk_size=200):
        self.video_path = video_path
        self.chunk_size = chunk_size
        cap = cv2.VideoCapture(video_path)
        self.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        self.width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()

    def __iter__(self):
        """Yield (chunk_frames, start_idx) pairs until the video is exhausted."""
        cap = cv2.VideoCapture(self.video_path)
        chunk = []
        start_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                if chunk:
                    yield chunk, start_idx
                break
            chunk.append(frame)
            if len(chunk) == self.chunk_size:
                yield chunk, start_idx
                start_idx += len(chunk)
                chunk = []
        cap.release()


class VideoWriter:
    """Streams processed frames to an output video file without holding all in RAM."""

    def __init__(self, output_path, fps, width, height):
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        ext = os.path.splitext(output_path)[1].lower()
        fourcc = cv2.VideoWriter_fourcc(*('mp4v' if ext == '.mp4' else 'XVID'))
        self._writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    def write_chunk(self, frames):
        for frame in frames:
            self._writer.write(frame)

    def release(self):
        self._writer.release()
