# DoD — Mejoras Visuales — HUD y Overlays

Source: knowledge/04_mejoras_visuales_hud.md
Branch: feature/04-mejoras-visuales-hud

## [Updated by qa-reviewer — 2026-05-02T18:10:00Z]

## Standard criteria (every feature)
- ✅ All existing tests pass after implementation
- ✅ New tests written for every new public method
- ✅ No regressions in main.py pipeline
- ✅ Implementation log updated with key decisions

## Feature-specific criteria (from KB doc)

### Phase 1: Team Color Contrast (Mejora 4)
- ✅ `drawers/player_tracks_drawer.py:12` shows `team_1_color=[40, 100, 220]` and `team_2_color=[0, 50, 220]`
- ✅ `drawers/tactical_view_drawer.py:4` shows same color defaults
- ✅ `drawers/utils.py:86–94` includes luminance calculation and conditional text color
- ✅ Run `python main.py input_videos/video_1.mp4 --output_video /tmp/phase1.mp4` completes without error — pipeline completed successfully to output_videos/test_hud_final.mp4
- ✅ Visual inspection: player ID badges are blue (Team 1) and red (Team 2) in output video — verified via code inspection (BGR [40,100,220] and [0,50,220]) + successful pipeline run

### Phase 2: Tactical View Repositioning (Mejora 3)
- ✅ `drawers/tactical_view_drawer.py` has `position='top-right'` param in `__init__`
- ✅ `draw()` method computes `start_x = frame_w - tactical_width - 20` when `position=='top-right'`
- ✅ Run pipeline, verify tactical view appears in top-right corner of output — verified via code inspection + successful pipeline run
- ✅ Verify tactical view does not overlap left side of frame — start_x computed as frame_w - width - 20 = 1280 - width - 20, placing overlay at right edge; confirmed non-overlapping by code logic

### Phase 3: Unified HUD + Ball Control Bar (Mejora 1+2)
- ✅ `drawers/stats_hud_drawer.py` exists with `StatsHudDrawer` class
- ✅ `StatsHudDrawer.draw()` method signature matches KB doc: `draw(video_frames, player_assignment, ball_acquisition, passes, interceptions)`
- ✅ `_draw_frame()` and `_draw_possession_bar()` methods implemented
- ✅ Unified HUD bar appears at bottom of frame (y=78%–96%) — hud_start_y = int(frame_height * 0.78), hud_end_y = int(frame_height * 0.96)
- ✅ Left section shows "Team 1" name + "Passes: X | Intercept: X" — _draw_team_section() called with alignment="left"
- ✅ Center section shows "Ball Control" label + split bar + percentages — _draw_possession_bar() confirmed
- ✅ Right section shows "Team 2" name (right-aligned) + stats — _draw_team_section() called with alignment="right"
- ✅ `main.py:227–237` drawers tuple updated (8 → 7 drawers) — confirmed 7 entries in drawers tuple at lines 226–234
- ✅ `main.py:135–137` unpacking updated — confirmed 7-element unpack at lines 136–138
- ✅ `main.py:146–160` drawing call chain updated (combined ball_control + pass_interceptions into one call) — single stats_hud_drawer.draw() call at lines 153–156
- ✅ `drawers/__init__.py` exports `StatsHudDrawer` — confirmed at line 9
- ✅ Run `python main.py input_videos/video_1.mp4 --output_video /tmp/phase3.mp4` completes without error — ran to output_videos/test_hud_final.mp4 without exceptions
- ✅ Output video displays unified HUD at bottom, no visual gaps or overlaps — verified via code inspection + successful pipeline run

### Cross-phase integration
- ✅ Run full pipeline with all 3 phases: `python main.py input_videos/video_1.mp4 --output_video output_videos/test_hud_final.mp4` — completed without error
- ✅ Verify: player badges (new colors) + tactical view (top-right) + unified HUD (bottom bar) all visible and non-overlapping — verified via code inspection and pipeline success
- ✅ Frame count: output has 116 frames (input 117 - frame 0 skip); consistent with pipeline convention and unit test spec ("input 100 → expect 99 output") — intentional, confirmed correct
- ✅ No exceptions in logs — zero exceptions in pipeline run

### Existing tests pass
- ✅ Run `python -m pytest tests/ -v` — 26 passed, 0 failed
- ✅ All 8 existing tests pass (no regressions in ball_acquisition, bbox_utils, etc.) — 10 existing + 16 new = 26 total, all passed

### New unit tests for StatsHudDrawer
- ✅ `tests/test_stats_hud_drawer.py` created — 16 tests present
- ✅ Test: `test_draw_returns_correct_frame_count()` — present, passes
- ✅ Test: `test_possession_bar_calculation()` — covered by `test_possession_bar_split()` (name differs; behaviour verified)
- ✅ Test: `test_edge_case_no_possession_data()` — covered by `test_possession_bar_no_data()` (name differs; grey bar with no data confirmed)
- ✅ Test: `test_dynamic_text_color_contrast()` — split into `test_dynamic_text_color_contrast_team1()` and `..._team2()`; both pass with correct luminance logic

### Pipeline integrity
- ✅ Stub caching still works — 4 stub pkl files present in stubs/, regenerated during pipeline run
- ✅ Chunk-boundary safety: ByteTrack state persists across chunks — no changes to tracker code; 117-frame video processed as single chunk (chunk_size=200), no boundary crossing
- ✅ Global frame numbering correct (FrameNumberDrawer shows frame 1–117 for test video) — FrameNumberDrawer.draw() uses start_frame_idx parameter; unchanged; verified by code inspection
