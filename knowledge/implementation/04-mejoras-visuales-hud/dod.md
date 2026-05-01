# DoD — Mejoras Visuales — HUD y Overlays

Source: knowledge/04_mejoras_visuales_hud.md
Branch: feature/04-mejoras-visuales-hud

## Standard criteria (every feature)
- [ ] All existing tests pass after implementation
- [ ] New tests written for every new public method
- [ ] No regressions in main.py pipeline
- [ ] Implementation log updated with key decisions

## Feature-specific criteria (from KB doc)

### Phase 1: Team Color Contrast (Mejora 4)
- [ ] `drawers/player_tracks_drawer.py:12` shows `team_1_color=[40, 100, 220]` and `team_2_color=[0, 50, 220]`
- [ ] `drawers/tactical_view_drawer.py:4` shows same color defaults
- [ ] `drawers/utils.py:86–94` includes luminance calculation and conditional text color
- [ ] Run `python main.py input_videos/video_1.mp4 --output_video /tmp/phase1.mp4` completes without error
- [ ] Visual inspection: player ID badges are blue (Team 1) and red (Team 2) in output video

### Phase 2: Tactical View Repositioning (Mejora 3)
- [ ] `drawers/tactical_view_drawer.py` has `position='top-right'` param in `__init__`
- [ ] `draw()` method computes `start_x = frame_w - tactical_width - 20` when `position=='top-right'`
- [ ] Run pipeline, verify tactical view appears in top-right corner of output
- [ ] Verify tactical view does not overlap left side of frame (where real game scoreboard typically is)

### Phase 3: Unified HUD + Ball Control Bar (Mejora 1+2)
- [ ] `drawers/stats_hud_drawer.py` exists with `StatsHudDrawer` class
- [ ] `StatsHudDrawer.draw()` method signature matches KB doc: `draw(video_frames, player_assignment, ball_acquisition, passes, interceptions)`
- [ ] `_draw_frame()` and `_draw_possession_bar()` methods implemented
- [ ] Unified HUD bar appears at bottom of frame (y=78%–96%)
- [ ] Left section shows "Team 1" name + "Passes: X | Intercept: X"
- [ ] Center section shows "Ball Control" label + split bar + percentages
- [ ] Right section shows "Team 2" name (right-aligned) + stats
- [ ] `main.py:227–237` drawers tuple updated (8 → 7 drawers)
- [ ] `main.py:135–137` unpacking updated
- [ ] `main.py:146–160` drawing call chain updated (combined ball_control + pass_interceptions into one call)
- [ ] `drawers/__init__.py` exports `StatsHudDrawer`
- [ ] Run `python main.py input_videos/video_1.mp4 --output_video /tmp/phase3.mp4` completes without error
- [ ] Output video displays unified HUD at bottom, no visual gaps or overlaps

### Cross-phase integration
- [ ] Run full pipeline with all 3 phases: `python main.py input_videos/video_1.mp4 --output_video output_videos/test_hud_final.mp4`
- [ ] Verify: player badges (new colors) + tactical view (top-right) + unified HUD (bottom bar) all visible and non-overlapping
- [ ] Frame count matches input (117 frames for video_1.mp4)
- [ ] No exceptions in logs

### Existing tests pass
- [ ] Run `python -m pytest tests/ -v`
- [ ] All 8 existing tests pass (no regressions in ball_acquisition, bbox_utils, etc.)

### New unit tests for StatsHudDrawer
- [ ] `tests/test_stats_hud_drawer.py` created
- [ ] Test: `test_draw_returns_correct_frame_count()` — input 100 frames, expect 99 output (skips frame 0)
- [ ] Test: `test_possession_bar_calculation()` — mock data with known possession split, verify bar proportions
- [ ] Test: `test_edge_case_no_possession_data()` — all frames with `ball_acquisition=-1`, verify gray bar with "–" rendered
- [ ] Test: `test_dynamic_text_color_contrast()` — verify luminance logic produces readable text on both team colors

### Pipeline integrity
- [ ] Stub caching still works (delete stubs, re-run, verify stubs regenerated)
- [ ] Chunk-boundary safety: ByteTrack state persists across chunks (player IDs continuous)
- [ ] Global frame numbering correct (FrameNumberDrawer shows frame 1–117 for test video)
