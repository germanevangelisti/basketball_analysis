import os
import argparse
import logging
import sys

from utils import read_stub, save_stub
from utils.video_utils import VideoReader, VideoWriter
from utils.config_manager import ConfigManager
from trackers import PlayerTracker, BallTracker
from team_assigner import TeamAssigner
from court_keypoint_detector import CourtKeypointDetector
from ball_aquisition import BallAquisitionDetector
from pass_and_interception_detector import PassAndInterceptionDetector
from tactical_view_converter import TacticalViewConverter
from speed_and_distance_calculator import SpeedAndDistanceCalculator
from drawers import (
    PlayerTracksDrawer,
    BallTracksDrawer,
    CourtKeypointDrawer,
    TeamBallControlDrawer,
    FrameNumberDrawer,
    PassInterceptionDrawer,
    TacticalViewDrawer,
    SpeedAndDistanceDrawer,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def parse_args():
    config = ConfigManager().config
    parser = argparse.ArgumentParser(description='Basketball Video Analysis')
    parser.add_argument('input_video', type=str, help='Path to input video file')
    parser.add_argument('--output_video', type=str,
                        default=config.get('output_video_path', 'output_videos/output_video.avi'))
    parser.add_argument('--stub_path', type=str,
                        default=config.get('stubs_default_path', 'stubs'))
    parser.add_argument('--chunk_size', type=int,
                        default=config.get('chunk_size', 200),
                        help='Frames per chunk during streaming (default: 200)')
    parser.add_argument('--no_stubs', action='store_true',
                        help='Ignore existing stubs and re-run all detections')
    return parser.parse_args()


def _load_all_stubs(stub_dir, total_frames):
    """Try to load all four detection stubs. Returns None if any is missing or mismatched."""
    names = {
        'player_tracks': 'player_track_stubs.pkl',
        'ball_tracks': 'ball_track_stubs.pkl',
        'court_keypoints': 'court_key_points_stub.pkl',
        'player_assignment': 'player_assignment_stub.pkl',
    }
    stubs = {}
    for key, fname in names.items():
        data = read_stub(True, os.path.join(stub_dir, fname))
        if data is None or len(data) != total_frames:
            return None
        stubs[key] = data
    return stubs


def _save_all_stubs(stub_dir, player_tracks, ball_tracks, court_keypoints, player_assignment):
    save_stub(os.path.join(stub_dir, 'player_track_stubs.pkl'), player_tracks)
    save_stub(os.path.join(stub_dir, 'ball_track_stubs.pkl'), ball_tracks)
    save_stub(os.path.join(stub_dir, 'court_key_points_stub.pkl'), court_keypoints)
    save_stub(os.path.join(stub_dir, 'player_assignment_stub.pkl'), player_assignment)


def _detection_pass(reader, player_tracker, ball_tracker, court_detector, team_assigner):
    """Stream video once, accumulate all lightweight detection results."""
    player_tracks, ball_tracks, court_keypoints, player_assignment = [], [], [], []

    for chunk_frames, start_idx in reader:
        end_idx = start_idx + len(chunk_frames)
        logger.info(f"  Detection: frames {start_idx + 1}–{end_idx} / {reader.total_frames}")

        pt = player_tracker.track_chunk(chunk_frames)
        bt = ball_tracker.detect_chunk(chunk_frames)
        ck = court_detector.detect_chunk(chunk_frames)
        pa = team_assigner.assign_chunk(chunk_frames, pt, start_idx)

        player_tracks.extend(pt)
        ball_tracks.extend(bt)
        court_keypoints.extend(ck)
        player_assignment.extend(pa)

    return player_tracks, ball_tracks, court_keypoints, player_assignment


def _analysis(player_tracks, ball_tracks, court_keypoints, player_assignment,
               ball_tracker, tactical_converter, speed_calculator, pass_detector):
    """Run all stateless analysis on the accumulated lightweight data."""
    logger.info("Ball track post-processing...")
    ball_tracks = ball_tracker.remove_wrong_detections(ball_tracks)
    ball_tracks = ball_tracker.interpolate_ball_positions(ball_tracks)

    logger.info("Tactical view transformation...")
    court_keypoints = tactical_converter.validate_keypoints(court_keypoints)
    tactical_positions = tactical_converter.transform_players_to_tactical_view(
        court_keypoints, player_tracks
    )

    logger.info("Ball possession detection...")
    ball_acquisition = BallAquisitionDetector().detect_ball_possession(player_tracks, ball_tracks)

    logger.info("Pass and interception detection...")
    passes = pass_detector.detect_passes(ball_acquisition, player_assignment)
    interceptions = pass_detector.detect_interceptions(ball_acquisition, player_assignment)

    logger.info("Speed and distance calculation...")
    distances = speed_calculator.calculate_distance(tactical_positions)
    speeds = speed_calculator.calculate_speed(distances)

    return {
        'ball_tracks': ball_tracks,
        'court_keypoints': court_keypoints,
        'tactical_positions': tactical_positions,
        'ball_acquisition': ball_acquisition,
        'passes': passes,
        'interceptions': interceptions,
        'distances': distances,
        'speeds': speeds,
    }


def _drawing_pass(reader, player_tracks, player_assignment, results,
                  tactical_converter, drawers, output_path):
    """Stream video a second time, draw overlays chunk by chunk, write to output."""
    (player_tracks_drawer, ball_tracks_drawer, court_keypoint_drawer,
     team_ball_control_drawer, frame_number_drawer, pass_interceptions_drawer,
     tactical_view_drawer, speed_and_distance_drawer) = drawers

    writer = VideoWriter(output_path, fps=24, width=reader.width, height=reader.height)

    for chunk_frames, start_idx in reader:
        end_idx = start_idx + len(chunk_frames)
        logger.info(f"  Drawing: frames {start_idx + 1}–{end_idx} / {reader.total_frames}")
        s = slice(start_idx, end_idx)

        out = player_tracks_drawer.draw(
            chunk_frames, player_tracks[s], player_assignment[s], results['ball_acquisition'][s]
        )
        out = ball_tracks_drawer.draw(out, results['ball_tracks'][s])
        out = court_keypoint_drawer.draw(out, results['court_keypoints'][s])
        out = frame_number_drawer.draw(out, start_frame_idx=start_idx)
        out = team_ball_control_drawer.draw(
            out, player_assignment[s], results['ball_acquisition'][s]
        )
        out = pass_interceptions_drawer.draw(
            out, results['passes'][s], results['interceptions'][s]
        )
        out = speed_and_distance_drawer.draw(
            out, player_tracks[s], results['distances'][s], results['speeds'][s]
        )
        out = tactical_view_drawer.draw(
            out,
            tactical_converter.court_image_path,
            tactical_converter.width,
            tactical_converter.height,
            tactical_converter.key_points,
            results['tactical_positions'][s],
            player_assignment[s],
            results['ball_acquisition'][s],
        )
        writer.write_chunk(out)

    writer.release()


def main():
    args = parse_args()
    config = ConfigManager()

    logger.info(f"Starting analysis: {args.input_video}")
    reader = VideoReader(args.input_video, chunk_size=args.chunk_size)
    logger.info(
        f"Video: {reader.total_frames} frames, {reader.fps:.1f} fps, "
        f"{reader.width}x{reader.height}, chunk_size={args.chunk_size}"
    )

    player_tracker = PlayerTracker(config.get('player_detector_path'))
    ball_tracker = BallTracker(config.get('ball_detector_path'))
    court_detector = CourtKeypointDetector(config.get('court_keypoint_detector_path'))
    team_assigner = TeamAssigner()

    # Pass 1: detection — from stubs if valid, otherwise stream the video
    stubs = None if args.no_stubs else _load_all_stubs(args.stub_path, reader.total_frames)

    if stubs:
        logger.info("Loaded all detections from stubs.")
        player_tracks = stubs['player_tracks']
        ball_tracks = stubs['ball_tracks']
        court_keypoints = stubs['court_keypoints']
        player_assignment = stubs['player_assignment']
    else:
        logger.info("Running detection pass (streaming)...")
        player_tracks, ball_tracks, court_keypoints, player_assignment = _detection_pass(
            reader, player_tracker, ball_tracker, court_detector, team_assigner
        )
        _save_all_stubs(
            args.stub_path, player_tracks, ball_tracks, court_keypoints, player_assignment
        )

    # Analysis on accumulated lightweight data (no frames in RAM)
    tactical_converter = TacticalViewConverter(court_image_path="./images/basketball_court.png")
    speed_calculator = SpeedAndDistanceCalculator(
        tactical_converter.width,
        tactical_converter.height,
        tactical_converter.actual_width_in_meters,
        tactical_converter.actual_height_in_meters,
    )
    pass_detector = PassAndInterceptionDetector()

    logger.info("Running analysis...")
    results = _analysis(
        player_tracks, ball_tracks, court_keypoints, player_assignment,
        ball_tracker, tactical_converter, speed_calculator, pass_detector,
    )

    # Pass 2: drawing — stream video again, draw chunk by chunk, write output
    drawers = (
        PlayerTracksDrawer(),
        BallTracksDrawer(),
        CourtKeypointDrawer(),
        TeamBallControlDrawer(),
        FrameNumberDrawer(),
        PassInterceptionDrawer(),
        TacticalViewDrawer(),
        SpeedAndDistanceDrawer(),
    )

    logger.info("Running drawing pass (streaming)...")
    _drawing_pass(
        reader, player_tracks, player_assignment, results,
        tactical_converter, drawers, args.output_video,
    )

    logger.info(f"Done. Output: {args.output_video}")


if __name__ == '__main__':
    main()
