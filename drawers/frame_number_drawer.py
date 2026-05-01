import cv2


class FrameNumberDrawer:
    def __init__(self):
        pass

    def draw(self, frames, start_frame_idx=0):
        output_frames = []
        for i, frame in enumerate(frames):
            frame = frame.copy()
            global_frame_num = start_frame_idx + i
            cv2.putText(frame, str(global_frame_num), (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            output_frames.append(frame)
        return output_frames
