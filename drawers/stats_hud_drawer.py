import cv2
import numpy as np


class StatsHudDrawer:
    """
    A unified HUD drawer combining team statistics and ball control visualization.
    Displays a bottom bar with three sections: Team 1 stats | Ball Control bar | Team 2 stats
    """

    def __init__(self, team_1_color=[40, 100, 220], team_2_color=[0, 50, 220],
                 team_1_name="Team 1", team_2_name="Team 2"):
        """
        Initialize the StatsHudDrawer.

        Args:
            team_1_color (list): BGR color for Team 1. Defaults to [40, 100, 220] (steel-blue).
            team_2_color (list): BGR color for Team 2. Defaults to [0, 50, 220] (vivid-red).
            team_1_name (str): Display name for Team 1.
            team_2_name (str): Display name for Team 2.
        """
        self.team_1_color = team_1_color
        self.team_2_color = team_2_color
        self.team_1_name = team_1_name
        self.team_2_name = team_2_name

    def get_team_ball_control(self, player_assignment, ball_acquisition):
        """
        Calculate which team has ball control for each frame.

        Args:
            player_assignment (list): List of dicts mapping player_id → team for each frame.
            ball_acquisition (list): List of player IDs with ball per frame (-1 if no possession).

        Returns:
            numpy.ndarray: Array indicating which team has ball control (1/2/-1) per frame.
        """
        team_ball_control = []
        for player_assignment_frame, ball_acquisition_frame in zip(player_assignment, ball_acquisition):
            if ball_acquisition_frame == -1:
                team_ball_control.append(-1)
                continue
            if ball_acquisition_frame not in player_assignment_frame:
                team_ball_control.append(-1)
                continue
            if player_assignment_frame[ball_acquisition_frame] == 1:
                team_ball_control.append(1)
            else:
                team_ball_control.append(2)

        return np.array(team_ball_control)

    def get_stats(self, passes, interceptions):
        """
        Calculate pass and interception counts for each team.

        Args:
            passes (list): List of ints (1/2 for team, 0 for no pass).
            interceptions (list): List of ints (1/2 for team, 0 for no interception).

        Returns:
            tuple: (team1_passes, team2_passes, team1_interceptions, team2_interceptions)
        """
        team1_passes = sum(1 for p in passes if p == 1)
        team2_passes = sum(1 for p in passes if p == 2)
        team1_interceptions = sum(1 for i in interceptions if i == 1)
        team2_interceptions = sum(1 for i in interceptions if i == 2)

        return team1_passes, team2_passes, team1_interceptions, team2_interceptions

    def draw(self, video_frames, player_assignment, ball_acquisition, passes, interceptions):
        """
        Draw unified HUD on a list of video frames.

        Args:
            video_frames (list): List of frames to draw on.
            player_assignment (list): List of dicts mapping player_id → team per frame.
            ball_acquisition (list): List of player IDs with ball per frame.
            passes (list): List of pass events (1/2/0) per frame.
            interceptions (list): List of interception events (1/2/0) per frame.

        Returns:
            list: List of frames with HUD drawn (skips frame 0).
        """
        team_ball_control = self.get_team_ball_control(player_assignment, ball_acquisition)

        output_video_frames = []
        for frame_num, frame in enumerate(video_frames):
            if frame_num == 0:
                continue

            frame_drawn = self._draw_frame(
                frame, frame_num, player_assignment, ball_acquisition,
                passes, interceptions, team_ball_control
            )
            output_video_frames.append(frame_drawn)

        return output_video_frames

    def _draw_frame(self, frame, frame_num, player_assignment, ball_acquisition,
                    passes, interceptions, team_ball_control):
        """
        Draw HUD overlay on a single frame.

        Args:
            frame: The video frame to draw on.
            frame_num: Current frame index.
            player_assignment: List of team assignments per frame.
            ball_acquisition: List of ball possession per frame.
            passes: List of pass events per frame.
            interceptions: List of interception events per frame.
            team_ball_control: Precomputed array of team ball control per frame.

        Returns:
            The frame with HUD drawn.
        """
        frame = frame.copy()
        frame_height, frame_width = frame.shape[:2]

        # HUD dimensions (bottom bar)
        hud_start_y = int(frame_height * 0.78)
        hud_end_y = int(frame_height * 0.96)
        hud_height = hud_end_y - hud_start_y

        # Draw semi-transparent background
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, hud_start_y), (frame_width, hud_end_y), (30, 30, 30), -1)
        alpha = 0.85
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

        # Calculate section widths (33% each)
        section_width = frame_width // 3

        # Draw vertical separators
        cv2.line(frame, (section_width, hud_start_y), (section_width, hud_end_y), (100, 100, 100), 2)
        cv2.line(frame, (2 * section_width, hud_start_y), (2 * section_width, hud_end_y), (100, 100, 100), 2)

        # Get stats up to current frame
        passes_till_frame = passes[:frame_num + 1]
        interceptions_till_frame = interceptions[:frame_num + 1]
        team1_passes, team2_passes, team1_interceptions, team2_interceptions = self.get_stats(
            passes_till_frame, interceptions_till_frame
        )

        # Calculate ball control percentages
        ball_control_till_frame = team_ball_control[:frame_num + 1]
        valid_frames = (ball_control_till_frame != -1).sum()
        if valid_frames > 0:
            team_1_pct = (ball_control_till_frame == 1).sum() / valid_frames
            team_2_pct = (ball_control_till_frame == 2).sum() / valid_frames
        else:
            team_1_pct = 0.0
            team_2_pct = 0.0

        # LEFT SECTION: Team 1 stats
        self._draw_team_section(
            frame, 0, hud_start_y, section_width, hud_height,
            self.team_1_name, team1_passes, team1_interceptions, self.team_1_color, "left"
        )

        # CENTER SECTION: Ball control bar
        self._draw_possession_bar(
            frame, section_width, hud_start_y, section_width, hud_height,
            team_1_pct, team_2_pct
        )

        # RIGHT SECTION: Team 2 stats
        self._draw_team_section(
            frame, 2 * section_width, hud_start_y, section_width, hud_height,
            self.team_2_name, team2_passes, team2_interceptions, self.team_2_color, "right"
        )

        return frame

    def _draw_team_section(self, frame, x_offset, y_offset, width, height,
                           team_name, passes, interceptions, color, alignment="left"):
        """
        Draw a team stats section in the HUD.

        Args:
            frame: The frame to draw on.
            x_offset: X position of section start.
            y_offset: Y position of section start.
            width: Width of section.
            height: Height of section.
            team_name: Team display name.
            passes: Number of passes.
            interceptions: Number of interceptions.
            color: Team color (BGR).
            alignment: "left" or "right" for text alignment.
        """
        font_scale = 0.6
        font_thickness = 1
        font = cv2.FONT_HERSHEY_SIMPLEX

        # Team name (bold, colored)
        name_y = y_offset + int(height * 0.35)
        if alignment == "left":
            name_x = x_offset + int(width * 0.1)
        else:
            # For right-aligned, measure text width and position accordingly
            (text_width, text_height) = cv2.getTextSize(team_name, font, font_scale + 0.2, 2)[0]
            name_x = x_offset + width - text_width - int(width * 0.1)

        cv2.putText(frame, team_name, (name_x, name_y), font, font_scale + 0.2, color, 2)

        # Stats row (Passes | Intercept)
        stats_text = f"P: {passes} | I: {interceptions}"
        stats_y = y_offset + int(height * 0.75)
        if alignment == "left":
            stats_x = x_offset + int(width * 0.1)
        else:
            (text_width, _) = cv2.getTextSize(stats_text, font, font_scale, 1)[0]
            stats_x = x_offset + width - text_width - int(width * 0.1)

        cv2.putText(frame, stats_text, (stats_x, stats_y), font, font_scale, (200, 200, 200), 1)

    def _draw_possession_bar(self, frame, x_offset, y_offset, width, height,
                              team_1_pct, team_2_pct):
        """
        Draw the ball control split bar in the center section.

        Args:
            frame: The frame to draw on.
            x_offset: X position of section start.
            y_offset: Y position of section start.
            width: Width of section.
            height: Height of section.
            team_1_pct: Team 1 possession percentage (0–1).
            team_2_pct: Team 2 possession percentage (0–1).
        """
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.55
        font_thickness = 1

        # Bar dimensions
        bar_margin_x = int(width * 0.1)
        bar_width = width - 2 * bar_margin_x
        bar_height = 15
        bar_x1 = x_offset + bar_margin_x
        bar_x2 = x_offset + width - bar_margin_x
        bar_y_center = y_offset + int(height * 0.5)
        bar_y1 = bar_y_center - bar_height // 2
        bar_y2 = bar_y_center + bar_height // 2

        # If no valid possession data, draw gray bar with "–"
        if team_1_pct == 0 and team_2_pct == 0:
            cv2.rectangle(frame, (bar_x1, bar_y1), (bar_x2, bar_y2), (100, 100, 100), -1)
            cv2.rectangle(frame, (bar_x1, bar_y1), (bar_x2, bar_y2), (150, 150, 150), 2)
            label_x = x_offset + width // 2 - 8
            label_y = y_offset + int(height * 0.3)
            cv2.putText(frame, "Ball Control", (label_x - 40, label_y), font, font_scale, (200, 200, 200), 1)
            cv2.putText(frame, "–", (x_offset + width // 2 - 5, bar_y_center + 6), font, 0.7, (150, 150, 150), 1)
        else:
            # Draw label
            label_x = x_offset + width // 2 - 50
            label_y = y_offset + int(height * 0.3)
            cv2.putText(frame, "Ball Control", (label_x, label_y), font, font_scale, (200, 200, 200), 1)

            # Calculate split position
            split_x = int(bar_x1 + bar_width * team_1_pct)

            # Draw Team 1 section
            cv2.rectangle(frame, (bar_x1, bar_y1), (split_x, bar_y2), self.team_1_color, -1)

            # Draw Team 2 section
            cv2.rectangle(frame, (split_x, bar_y1), (bar_x2, bar_y2), self.team_2_color, -1)

            # Border
            cv2.rectangle(frame, (bar_x1, bar_y1), (bar_x2, bar_y2), (150, 150, 150), 2)

            # Percentage labels
            pct_y = y_offset + int(height * 0.75)

            # Team 1 percentage (left-aligned)
            pct_1_text = f"{team_1_pct * 100:.0f}%"
            cv2.putText(frame, pct_1_text, (bar_x1 + 5, pct_y), font, font_scale, (200, 200, 200), 1)

            # Team 2 percentage (right-aligned)
            pct_2_text = f"{team_2_pct * 100:.0f}%"
            (text_width, _) = cv2.getTextSize(pct_2_text, font, font_scale, 1)[0]
            cv2.putText(frame, pct_2_text, (bar_x2 - text_width - 5, pct_y), font, font_scale, (200, 200, 200), 1)
