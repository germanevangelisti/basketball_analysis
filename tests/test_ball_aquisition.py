import sys
import os
import pytest
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ball_aquisition.ball_aquisition_detector import BallAquisitionDetector

class TestBallAquisitionDetector:
    def setup_method(self):
        self.detector = BallAquisitionDetector()

    def test_calculate_ball_containment_ratio_full(self):
        player_bbox = (0, 0, 100, 100)
        ball_bbox = (20, 20, 40, 40) # Fully inside
        ratio = self.detector.calculate_ball_containment_ratio(player_bbox, ball_bbox)
        assert ratio == 1.0

    def test_calculate_ball_containment_ratio_none(self):
        player_bbox = (0, 0, 100, 100)
        ball_bbox = (200, 200, 220, 220) # Fully outside
        ratio = self.detector.calculate_ball_containment_ratio(player_bbox, ball_bbox)
        assert ratio == 0.0

    def test_calculate_ball_containment_ratio_partial(self):
        player_bbox = (0, 0, 100, 100)
        # Ball 20x20. Half in, half out.
        # Ball x range 90 to 110. y range 0 to 20.
        # Intersection: x 90-100 (10), y 0-20 (20). Area = 200.
        # Ball Area: 20*20 = 400.
        # Ratio = 0.5
        ball_bbox = (90, 0, 110, 20)
        ratio = self.detector.calculate_ball_containment_ratio(player_bbox, ball_bbox)
        assert ratio == 0.5

    def test_find_best_candidate_high_containment(self):
        ball_center = (50, 50)
        ball_bbox = (40, 40, 60, 60)

        # Player 1 contains the ball
        player_tracks = {
            1: {'bbox': (0, 0, 100, 100)},
            2: {'bbox': (200, 200, 300, 300)}
        }

        candidate = self.detector.find_best_candidate_for_possession(ball_center, player_tracks, ball_bbox)
        assert candidate == 1

    def test_find_best_candidate_distance(self):
        # Ball not contained by anyone, but close to Player 2
        ball_center = (200, 200)
        ball_bbox = (190, 190, 210, 210)

        # Player 2 bbox is (205, 205, 300, 300).
        # Ball center (200,200).
        # Nearest point on Player 2 bbox to (200,200) is (205,205). Dist ~ 7.07
        # Threshold is 50. So Player 2 should get it.

        player_tracks = {
            1: {'bbox': (0, 0, 100, 100)}, # Far away
            2: {'bbox': (205, 205, 300, 300)} # Close
        }

        candidate = self.detector.find_best_candidate_for_possession(ball_center, player_tracks, ball_bbox)
        assert candidate == 2
