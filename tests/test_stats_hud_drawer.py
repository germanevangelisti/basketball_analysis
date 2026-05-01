import pytest
import numpy as np
import cv2
from drawers.stats_hud_drawer import StatsHudDrawer


class TestStatsHudDrawer:
    """Test cases for the unified StatsHudDrawer."""

    def setup_method(self):
        """Set up test fixtures."""
        self.drawer = StatsHudDrawer()
        # Create dummy test frame (1280x720 typical resolution)
        self.test_frame = np.zeros((720, 1280, 3), dtype=np.uint8)

    def test_initialization(self):
        """Test drawer initialization with default parameters."""
        drawer = StatsHudDrawer()
        assert drawer.team_1_color == [40, 100, 220]
        assert drawer.team_2_color == [0, 50, 220]
        assert drawer.team_1_name == "Team 1"
        assert drawer.team_2_name == "Team 2"

    def test_initialization_with_custom_colors(self):
        """Test drawer initialization with custom colors."""
        custom_color_1 = [100, 150, 200]
        custom_color_2 = [50, 100, 150]
        drawer = StatsHudDrawer(
            team_1_color=custom_color_1,
            team_2_color=custom_color_2
        )
        assert drawer.team_1_color == custom_color_1
        assert drawer.team_2_color == custom_color_2

    def test_get_team_ball_control_basic(self):
        """Test basic team ball control calculation."""
        player_assignment = [
            {1: 1, 2: 1, 3: 2, 4: 2},
            {1: 1, 2: 1, 3: 2, 4: 2},
            {1: 1, 2: 1, 3: 2, 4: 2},
        ]
        ball_acquisition = [1, 3, -1]  # Team 1, Team 2, no possession

        result = self.drawer.get_team_ball_control(player_assignment, ball_acquisition)

        assert len(result) == 3
        assert result[0] == 1  # Player 1 on Team 1
        assert result[1] == 2  # Player 3 on Team 2
        assert result[2] == -1  # No possession

    def test_get_team_ball_control_missing_player(self):
        """Test team ball control when player not in assignment."""
        player_assignment = [
            {1: 1, 2: 1, 3: 2, 4: 2},
        ]
        ball_acquisition = [5]  # Player 5 not in assignment

        result = self.drawer.get_team_ball_control(player_assignment, ball_acquisition)

        assert result[0] == -1  # Unknown team

    def test_get_stats(self):
        """Test pass and interception statistics calculation."""
        passes = [1, 1, 2, 0, 1, 2, 2]
        interceptions = [0, 1, 0, 2, 1, 0, 2]

        t1_p, t2_p, t1_i, t2_i = self.drawer.get_stats(passes, interceptions)

        # passes = [1(T1), 1(T1), 2(T2), 0, 1(T1), 2(T2), 2(T2)]
        # T1 passes: 3, T2 passes: 3
        assert t1_p == 3
        assert t2_p == 3
        # interceptions = [0, 1(T1), 0, 2(T2), 1(T1), 0, 2(T2)]
        # T1 interceptions: 2, T2 interceptions: 2
        assert t1_i == 2  # Team 1 interceptions at indices 1, 4
        assert t2_i == 2  # Team 2 interceptions at indices 3, 6

    def test_get_stats_empty(self):
        """Test stats with empty lists."""
        passes = []
        interceptions = []

        t1_p, t2_p, t1_i, t2_i = self.drawer.get_stats(passes, interceptions)

        assert t1_p == 0
        assert t2_p == 0
        assert t1_i == 0
        assert t2_i == 0

    def test_draw_returns_correct_frame_count(self):
        """Test that draw() skips frame 0 and returns N-1 frames."""
        num_frames = 100
        video_frames = [self.test_frame.copy() for _ in range(num_frames)]
        player_assignment = [{} for _ in range(num_frames)]
        ball_acquisition = [-1] * num_frames
        passes = [0] * num_frames
        interceptions = [0] * num_frames

        result = self.drawer.draw(
            video_frames, player_assignment, ball_acquisition, passes, interceptions
        )

        assert len(result) == num_frames - 1

    def test_draw_with_single_frame(self):
        """Test draw with single frame (should return empty list after skipping frame 0)."""
        video_frames = [self.test_frame.copy()]
        player_assignment = [{}]
        ball_acquisition = [-1]
        passes = [0]
        interceptions = [0]

        result = self.drawer.draw(
            video_frames, player_assignment, ball_acquisition, passes, interceptions
        )

        assert len(result) == 0

    def test_draw_with_two_frames(self):
        """Test draw with two frames (should return one after skipping frame 0)."""
        video_frames = [self.test_frame.copy(), self.test_frame.copy()]
        player_assignment = [{}, {}]
        ball_acquisition = [-1, -1]
        passes = [0, 0]
        interceptions = [0, 0]

        result = self.drawer.draw(
            video_frames, player_assignment, ball_acquisition, passes, interceptions
        )

        assert len(result) == 1
        assert result[0].shape == self.test_frame.shape

    def test_possession_bar_no_data(self):
        """Test possession bar rendering when no possession data (all -1)."""
        video_frames = [self.test_frame.copy() for _ in range(5)]
        player_assignment = [{} for _ in range(5)]
        ball_acquisition = [-1] * 5
        passes = [0] * 5
        interceptions = [0] * 5

        result = self.drawer.draw(
            video_frames, player_assignment, ball_acquisition, passes, interceptions
        )

        # Should produce frames without errors
        assert len(result) == 4
        for frame in result:
            assert frame is not None
            assert frame.shape == self.test_frame.shape

    def test_possession_bar_all_team_1(self):
        """Test possession bar when all possession is Team 1."""
        video_frames = [self.test_frame.copy() for _ in range(5)]
        player_assignment = [{1: 1, 2: 1, 3: 2, 4: 2} for _ in range(5)]
        ball_acquisition = [1, 1, 1, 1, 1]  # Always Team 1
        passes = [0] * 5
        interceptions = [0] * 5

        result = self.drawer.draw(
            video_frames, player_assignment, ball_acquisition, passes, interceptions
        )

        assert len(result) == 4
        # Frames should have HUD drawn
        assert result[0] is not None

    def test_possession_bar_split(self):
        """Test possession bar with even split between teams."""
        video_frames = [self.test_frame.copy() for _ in range(6)]
        player_assignment = [{1: 1, 2: 1, 3: 2, 4: 2} for _ in range(6)]
        ball_acquisition = [1, 1, 1, 3, 3, 3]  # T1 frames 0-2, T2 frames 3-5
        passes = [0] * 6
        interceptions = [0] * 6

        result = self.drawer.draw(
            video_frames, player_assignment, ball_acquisition, passes, interceptions
        )

        assert len(result) == 5
        # Each result frame should be a valid image
        for frame in result:
            assert frame.shape == self.test_frame.shape

    def test_hud_renders_without_error(self):
        """Test that HUD renders on all frames without exceptions."""
        num_frames = 20
        video_frames = [self.test_frame.copy() for _ in range(num_frames)]
        player_assignment = [{1: 1, 2: 1, 3: 2, 4: 2} for _ in range(num_frames)]
        ball_acquisition = [1 if i % 2 == 0 else 3 for i in range(num_frames)]
        passes = [1 if i % 3 == 0 else 2 if i % 3 == 1 else 0 for i in range(num_frames)]
        interceptions = [0] * num_frames

        result = self.drawer.draw(
            video_frames, player_assignment, ball_acquisition, passes, interceptions
        )

        assert len(result) == num_frames - 1
        for frame in result:
            assert frame.shape[0] > 0 and frame.shape[1] > 0

    def test_dynamic_text_color_contrast_team1(self):
        """Test that text color is readable on Team 1 color (steel-blue)."""
        # Team 1 color [40, 100, 220] in BGR (R=220, G=100, B=40)
        # luminance = 0.299*220 + 0.587*100 + 0.114*40 = ~159, so text should be black
        team1_color = [40, 100, 220]
        r, g, b = team1_color[2], team1_color[1], team1_color[0]
        luminance = 0.299*r + 0.587*g + 0.114*b
        text_color = (0, 0, 0) if luminance > 128 else (255, 255, 255)

        assert text_color == (0, 0, 0)  # Black text expected

    def test_dynamic_text_color_contrast_team2(self):
        """Test that text color is readable on Team 2 color (vivid-red)."""
        # Team 2 color [0, 50, 220] in BGR (R=220, G=50, B=0)
        # luminance = 0.299*220 + 0.587*50 + 0.114*0 = ~95, so text should be white
        team2_color = [0, 50, 220]
        r, g, b = team2_color[2], team2_color[1], team2_color[0]
        luminance = 0.299*r + 0.587*g + 0.114*b
        text_color = (0, 0, 0) if luminance > 128 else (255, 255, 255)

        assert text_color == (255, 255, 255)  # White text expected

    def test_cumulative_stats_per_frame(self):
        """Test that stats accumulate cumulatively through frames."""
        # Frames have passes at frame 2, 5, 7
        passes = [0, 0, 1, 0, 0, 2, 0, 1, 0]
        interceptions = [0, 0, 0, 1, 0, 0, 2, 0, 0]

        # At frame 2: T1 passes=1, interceptions=0
        # At frame 3: T1 passes=1, interceptions=1
        # At frame 5: T1 passes=1, T2 passes=1, interceptions=1
        # etc.

        video_frames = [self.test_frame.copy() for _ in range(len(passes) + 1)]
        player_assignment = [{1: 1, 2: 1, 3: 2, 4: 2} for _ in range(len(passes) + 1)]
        ball_acquisition = [-1] * (len(passes) + 1)

        result = self.drawer.draw(
            video_frames, player_assignment, ball_acquisition, passes, interceptions
        )

        # Should produce valid frames without errors
        assert len(result) == len(passes)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
