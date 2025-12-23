import os
import argparse
import logging
import sys
from utils import read_video, save_video
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
    SpeedAndDistanceDrawer
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def parse_args():
    # Load default config to get default paths
    config = ConfigManager().config

    parser = argparse.ArgumentParser(description='Basketball Video Analysis')
    parser.add_argument('input_video', type=str, help='Path to input video file')
    parser.add_argument('--output_video', type=str, default=config.get('output_video_path', 'output_videos/output_video.avi'),
                        help='Path to output video file')
    parser.add_argument('--stub_path', type=str, default=config.get('stubs_default_path', 'stubs'),
                        help='Path to stub directory')
    return parser.parse_args()

def main():
    args = parse_args()
    config = ConfigManager()

    logger.info(f"Starting analysis for video: {args.input_video}")
    
    # Read Video
    video_frames = read_video(args.input_video)
    
    ## Initialize Tracker
    logger.info("Initializing trackers...")
    player_tracker = PlayerTracker(config.get('player_detector_path'))
    ball_tracker = BallTracker(config.get('ball_detector_path'))

    ## Initialize Keypoint Detector
    court_keypoint_detector = CourtKeypointDetector(config.get('court_keypoint_detector_path'))

    # Run Detectors
    logger.info("Running player tracker...")
    player_tracks = player_tracker.get_object_tracks(video_frames,
                                       read_from_stub=True,
                                       stub_path=os.path.join(args.stub_path, 'player_track_stubs.pkl')
                                      )
    
    logger.info("Running ball tracker...")
    ball_tracks = ball_tracker.get_object_tracks(video_frames,
                                                 read_from_stub=True,
                                                 stub_path=os.path.join(args.stub_path, 'ball_track_stubs.pkl')
                                                )
    ## Run KeyPoint Extractor
    logger.info("Extracting court keypoints...")
    court_keypoints_per_frame = court_keypoint_detector.get_court_keypoints(video_frames,
                                                                    read_from_stub=True,
                                                                    stub_path=os.path.join(args.stub_path, 'court_key_points_stub.pkl')
                                                                    )

    # Remove Wrong Ball Detections
    ball_tracks = ball_tracker.remove_wrong_detections(ball_tracks)
    # Interpolate Ball Tracks
    ball_tracks = ball_tracker.interpolate_ball_positions(ball_tracks)
   

    # Assign Player Teams
    logger.info("Assigning player teams...")
    team_assigner = TeamAssigner()
    player_assignment = team_assigner.get_player_teams_across_frames(video_frames,
                                                                    player_tracks,
                                                                    read_from_stub=True,
                                                                    stub_path=os.path.join(args.stub_path, 'player_assignment_stub.pkl')
                                                                    )

    # Ball Acquisition
    logger.info("Detecting ball possession...")
    ball_aquisition_detector = BallAquisitionDetector()
    ball_aquisition = ball_aquisition_detector.detect_ball_possession(player_tracks,ball_tracks)

    # Detect Passes
    logger.info("Detecting passes and interceptions...")
    pass_and_interception_detector = PassAndInterceptionDetector()
    passes = pass_and_interception_detector.detect_passes(ball_aquisition,player_assignment)
    interceptions = pass_and_interception_detector.detect_interceptions(ball_aquisition,player_assignment)

    # Tactical View
    logger.info("Generating tactical view...")
    tactical_view_converter = TacticalViewConverter(
        court_image_path="./images/basketball_court.png"
    )

    court_keypoints_per_frame = tactical_view_converter.validate_keypoints(court_keypoints_per_frame)
    tactical_player_positions = tactical_view_converter.transform_players_to_tactical_view(court_keypoints_per_frame,player_tracks)

    # Speed and Distance Calculator
    logger.info("Calculating speed and distance...")
    speed_and_distance_calculator = SpeedAndDistanceCalculator(
        tactical_view_converter.width,
        tactical_view_converter.height,
        tactical_view_converter.actual_width_in_meters,
        tactical_view_converter.actual_height_in_meters
    )
    player_distances_per_frame = speed_and_distance_calculator.calculate_distance(tactical_player_positions)
    player_speed_per_frame = speed_and_distance_calculator.calculate_speed(player_distances_per_frame)

    # Draw output   
    logger.info("Drawing output video...")
    # Initialize Drawers
    player_tracks_drawer = PlayerTracksDrawer()
    ball_tracks_drawer = BallTracksDrawer()
    court_keypoint_drawer = CourtKeypointDrawer()
    team_ball_control_drawer = TeamBallControlDrawer()
    frame_number_drawer = FrameNumberDrawer()
    pass_and_interceptions_drawer = PassInterceptionDrawer()
    tactical_view_drawer = TacticalViewDrawer()
    speed_and_distance_drawer = SpeedAndDistanceDrawer()

    ## Draw object Tracks
    output_video_frames = player_tracks_drawer.draw(video_frames, 
                                                    player_tracks,
                                                    player_assignment,
                                                    ball_aquisition)
    output_video_frames = ball_tracks_drawer.draw(output_video_frames, ball_tracks)

    ## Draw KeyPoints
    output_video_frames = court_keypoint_drawer.draw(output_video_frames, court_keypoints_per_frame)

    ## Draw Frame Number
    output_video_frames = frame_number_drawer.draw(output_video_frames)

    # Draw Team Ball Control
    output_video_frames = team_ball_control_drawer.draw(output_video_frames,
                                                        player_assignment,
                                                        ball_aquisition)

    # Draw Passes and Interceptions
    output_video_frames = pass_and_interceptions_drawer.draw(output_video_frames,
                                                             passes,
                                                             interceptions)
    
    # Speed and Distance Drawer
    output_video_frames = speed_and_distance_drawer.draw(output_video_frames,
                                                         player_tracks,
                                                         player_distances_per_frame,
                                                         player_speed_per_frame
                                                         )

    ## Draw Tactical View
    output_video_frames = tactical_view_drawer.draw(output_video_frames,
                                                    tactical_view_converter.court_image_path,
                                                    tactical_view_converter.width,
                                                    tactical_view_converter.height,
                                                    tactical_view_converter.key_points,
                                                    tactical_player_positions,
                                                    player_assignment,
                                                    ball_aquisition,
                                                    )

    # Save video
    save_video(output_video_frames, args.output_video)
    logger.info(f"Video saved to {args.output_video}")

if __name__ == '__main__':
    main()
