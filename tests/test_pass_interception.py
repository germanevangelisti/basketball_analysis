import sys
import os
import pytest
from unittest.mock import MagicMock
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pass_and_interception_detector.pass_and_interception_detector import PassAndInterceptionDetector

class TestPassAndInterceptionDetector:
    def setup_method(self):
        self.detector = PassAndInterceptionDetector()

    def test_detect_passes_basic(self):
        # Frame 0-10: Player 1 has ball
        # Frame 11-20: No one
        # Frame 21-30: Player 2 has ball
        # Should detect a pass from 1 to 2

        possession_list = [-1] * 40
        for i in range(10): possession_list[i] = 1
        for i in range(21, 30): possession_list[i] = 2

        # Mock player assignment (List of dictionaries per frame)
        # Player 1: Team 1
        # Player 2: Team 1
        assignments_per_frame = {1: 1, 2: 1}
        player_assignment = [assignments_per_frame] * 40

        passes = self.detector.detect_passes(possession_list, player_assignment)

        # Passes is a list of len 40.
        # The detector returns a list where value > 0 indicates a pass occurred at that frame.
        pass_count = sum(1 for p in passes if p != -1)
        assert pass_count == 1

    def test_detect_interceptions_basic(self):
        # Player 1 (Team 1) -> No One -> Player 3 (Team 2)
        possession_list = [-1] * 40
        for i in range(10): possession_list[i] = 1
        for i in range(21, 30): possession_list[i] = 3

        assignments_per_frame = {1: 1, 3: 2}
        player_assignment = [assignments_per_frame] * 40

        interceptions = self.detector.detect_interceptions(possession_list, player_assignment)

        interception_count = sum(1 for i in interceptions if i != -1)
        assert interception_count == 1
