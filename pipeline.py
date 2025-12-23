import os
import logging
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

logger = logging.getLogger(__name__)

class GameAnalysisPipeline:
    """
    Orchestrates the basketball video analysis pipeline.
    """
    def __init__(self, config=None):
        self.config = config or ConfigManager()
        self._init_models()
        self._init_drawers()

    def _init_models(self):
        logger.info("Initializing models...")
        self.player_tracker = PlayerTracker(self.config.get('player_detector_path'))
        self.ball_tracker = BallTracker(self.config.get('ball_detector_path'))
        self.court_keypoint_detector = CourtKeypointDetector(self.config.get('court_keypoint_detector_path'))
        self.team_assigner = TeamAssigner()
        self.ball_aquisition_detector = BallAquisitionDetector()
        self.pass_and_interception_detector = PassAndInterceptionDetector()

        # Tactical View (hardcoded image path for now, could be in config)
        self.tactical_view_converter = TacticalViewConverter(
            court_image_path="./images/basketball_court.png"
        )

        # Speed calc depends on tactical view dimensions
        self.speed_and_distance_calculator = SpeedAndDistanceCalculator(
            self.tactical_view_converter.width,
            self.tactical_view_converter.height,
            self.tactical_view_converter.actual_width_in_meters,
            self.tactical_view_converter.actual_height_in_meters
        )

    def _init_drawers(self):
        logger.info("Initializing drawers...")
        self.player_tracks_drawer = PlayerTracksDrawer()
        self.ball_tracks_drawer = BallTracksDrawer()
        self.court_keypoint_drawer = CourtKeypointDrawer()
        self.team_ball_control_drawer = TeamBallControlDrawer()
        self.frame_number_drawer = FrameNumberDrawer()
        self.pass_and_interceptions_drawer = PassInterceptionDrawer()
        self.tactical_view_drawer = TacticalViewDrawer()
        self.speed_and_distance_drawer = SpeedAndDistanceDrawer()

    def run(self, input_video_path, output_video_path, stub_path=None):
        """
        Run the analysis pipeline on a video.
        """
        logger.info(f"Starting pipeline for {input_video_path}")

        if stub_path is None:
            stub_path = self.config.get('stubs_default_path', 'stubs')

        # 1. Read Video
        video_frames = read_video(input_video_path)

        # 2. Run Detectors
        logger.info("Running trackers...")
        player_tracks = self.player_tracker.get_object_tracks(
            video_frames,
            read_from_stub=True,
            stub_path=os.path.join(stub_path, 'player_track_stubs.pkl')
        )

        ball_tracks = self.ball_tracker.get_object_tracks(
            video_frames,
            read_from_stub=True,
            stub_path=os.path.join(stub_path, 'ball_track_stubs.pkl')
        )

        logger.info("Extracting keypoints...")
        court_keypoints_per_frame = self.court_keypoint_detector.get_court_keypoints(
            video_frames,
            read_from_stub=True,
            stub_path=os.path.join(stub_path, 'court_key_points_stub.pkl')
        )

        # 3. Process Ball Tracks
        ball_tracks = self.ball_tracker.remove_wrong_detections(ball_tracks)
        ball_tracks = self.ball_tracker.interpolate_ball_positions(ball_tracks)

        # 4. Assign Teams
        logger.info("Assigning teams...")
        player_assignment = self.team_assigner.get_player_teams_across_frames(
            video_frames,
            player_tracks,
            read_from_stub=True,
            stub_path=os.path.join(stub_path, 'player_assignment_stub.pkl')
        )

        # 5. Ball Acquisition
        logger.info("Detecting possession...")
        ball_aquisition = self.ball_aquisition_detector.detect_ball_possession(player_tracks, ball_tracks)

        # 6. Passes & Interceptions
        logger.info("Analyzing plays...")
        passes = self.pass_and_interception_detector.detect_passes(ball_aquisition, player_assignment)
        interceptions = self.pass_and_interception_detector.detect_interceptions(ball_aquisition, player_assignment)

        # 7. Tactical View & Stats
        logger.info("Calculating stats...")
        court_keypoints_per_frame = self.tactical_view_converter.validate_keypoints(court_keypoints_per_frame)
        tactical_player_positions = self.tactical_view_converter.transform_players_to_tactical_view(
            court_keypoints_per_frame, player_tracks
        )

        player_distances_per_frame = self.speed_and_distance_calculator.calculate_distance(tactical_player_positions)
        player_speed_per_frame = self.speed_and_distance_calculator.calculate_speed(player_distances_per_frame)

        # 8. Draw Output
        logger.info("Drawing results...")
        output_video_frames = self.player_tracks_drawer.draw(
            video_frames, player_tracks, player_assignment, ball_aquisition
        )
        output_video_frames = self.ball_tracks_drawer.draw(output_video_frames, ball_tracks)
        output_video_frames = self.court_keypoint_drawer.draw(output_video_frames, court_keypoints_per_frame)
        output_video_frames = self.frame_number_drawer.draw(output_video_frames)
        output_video_frames = self.team_ball_control_drawer.draw(output_video_frames, player_assignment, ball_aquisition)
        output_video_frames = self.pass_and_interceptions_drawer.draw(output_video_frames, passes, interceptions)
        output_video_frames = self.speed_and_distance_drawer.draw(
            output_video_frames, player_tracks, player_distances_per_frame, player_speed_per_frame
        )
        output_video_frames = self.tactical_view_drawer.draw(
            output_video_frames,
            self.tactical_view_converter.court_image_path,
            self.tactical_view_converter.width,
            self.tactical_view_converter.height,
            self.tactical_view_converter.key_points,
            tactical_player_positions,
            player_assignment,
            ball_aquisition,
        )

        # 9. Save
        save_video(output_video_frames, output_video_path)
        logger.info(f"Done! Saved to {output_video_path}")
