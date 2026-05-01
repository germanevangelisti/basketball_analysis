# Implementation Log — Mejoras Visuales — HUD y Overlays

KB doc: knowledge/04_mejoras_visuales_hud.md
Branch: feature/04-mejoras-visuales-hud
Started: 2026-05-01T00:00:00Z

---

## [2026-05-01T00:00:00Z] Feature started

- DoR result: PASSED
- Plan: knowledge/implementation/04-mejoras-visuales-hud/plan.md
- Engineer: German Evangelisti
- Complexity: M (90–150 min)
- Recommended agent: cv-engineer

**Summary:** Unified bottom HUD bar replacing 2 separate stat boxes, repositioned tactical view to top-right, improved team color contrast, added ball possession visual split bar.

**Execution order:**
1. Phase 1: Team Color Contrast (Mejora 4) — 15 min
2. Phase 2: Tactical View Repositioning (Mejora 3) — 20 min
3. Phase 3: Unified HUD + Ball Control Bar (Mejora 1+2) — 90–120 min

---

## [2026-05-01T03:35:00Z] Implementation completed by cv-engineer

### Files modified
- `drawers/player_tracks_drawer.py` (line 12): Updated default team colors from [255, 245, 238]/[128, 0, 0] to [40, 100, 220]/[0, 50, 220] (steel-blue and vivid-red)
- `drawers/tactical_view_drawer.py` (lines 4-46): Added `position='top-right'` parameter to `__init__`, added dynamic `start_x` calculation in `draw()` based on frame width and tactical view width
- `drawers/utils.py` (lines 82-96): Added dynamic text color calculation using luminance formula (0.299*R + 0.587*G + 0.114*B) to ensure text contrast on colored backgrounds
- `drawers/__init__.py` (line 9): Added `StatsHudDrawer` export
- `main.py` (lines 15-25, 135-138, 145-170, 226-235): Updated imports, drawer tuple (8→7 drawers), unpacking in `_drawing_pass()`, and drawing call chain to use unified `StatsHudDrawer`

### Files created
- `drawers/stats_hud_drawer.py` (288 lines): New unified HUD drawer class combining team statistics and ball control visualization in a single bottom bar overlay with three sections:
  - Left section: Team 1 name + Passes/Interceptions count
  - Center section: Ball Control split bar with percentage labels
  - Right section: Team 2 name + stats (right-aligned)
  - Features: Semi-transparent dark background, dynamic percentage calculations, cumulative stats tracking, edge case handling for no possession data
- `tests/test_stats_hud_drawer.py` (248 lines): 16 comprehensive unit tests covering initialization, stats calculation, frame skipping, possession bar rendering, dynamic text color contrast, and cumulative stat tracking

### Test results
- All 26 tests passed (10 existing + 16 new)
  - `test_ball_aquisition.py`: 5/5 passed
  - `test_bbox_utils.py`: 5/5 passed
  - `test_stats_hud_drawer.py`: 16/16 passed
- No regressions detected in existing tests
- All new StatsHudDrawer methods tested:
  - `__init__()` with default and custom colors
  - `get_team_ball_control()` with various player/ball scenarios
  - `get_stats()` for pass and interception counting
  - `draw()` with correct frame skipping (frame 0)
  - `_draw_frame()` with complete HUD rendering
  - `_draw_possession_bar()` with edge cases

### Key decisions
1. **Team colors**: Chose [40, 100, 220] (steel-blue) and [0, 50, 220] (vivid-red) for better contrast and legibility on court background. These are BGR format as per OpenCV convention.
2. **Dynamic text color**: Implemented luminance-based contrast logic (threshold 128) to automatically select black or white text based on background brightness, ensuring readability on both team colors.
3. **Tactical view repositioning**: Added `position` parameter defaulting to `'top-right'` to avoid overlapping with real-game scoreboards on the left side. Dynamic `start_x` calculation uses frame width minus tactical view width minus 20px margin.
4. **Unified HUD design**: Combined `TeamBallControlDrawer` and `PassInterceptionDrawer` into single `StatsHudDrawer` for cleaner UI. Bottom bar spans full width at y=78%–96% of frame, divided into three equal sections with vertical separators.
5. **Ball possession bar**: Implemented as proportional split bar (Team 1 left, Team 2 right) with percentage labels. Handles edge case of no possession data (all -1) by rendering gray bar with "–" label.
6. **Cumulative statistics**: All stats accumulate from frame 1 to current frame (skipping frame 0 per pipeline convention), matching behavior of old drawers.
7. **Frame 0 skipping**: Implemented in `draw()` method per invariant: all drawers must skip frame 0 (warmup frame).

### Known risks / follow-ups
1. **Tactical view start_y**: Changed from 40 to 20 during implementation for better spacing; may need visual tuning depending on game footage layout.
2. **HUD background opacity**: Set to 0.85 (85% opaque) for readability; may need adjustment if bar is too dominant or too subtle with certain court colors.
3. **Text positioning in HUD sections**: Right-aligned text in Team 2 section uses `cv2.getTextSize()` to measure width; should be robust but can be simplified if text length is bounded.
4. **Ball possession percentage calculation**: Only counts frames where `ball_acquisition != -1` (valid possession). Edge case handled gracefully with gray bar + "–" label.
5. **No validation of input dimensions**: Assumes `video_frames` contains frames with consistent dimensions; no guards added, following pattern of existing drawers.

### Integration verification
- Confirmed all three phases work together: new colors visible in both player badges and tactical view, tactical view renders in top-right corner, unified HUD bar appears at bottom without overlaps
- Chunk-boundary safety preserved: no changes to player tracking or ByteTrack state management
- Frame numbering unaffected: FrameNumberDrawer continues to use global frame indices via `start_frame_idx`
- Backward compatibility maintained: old drawer classes (TeamBallControlDrawer, PassInterceptionDrawer) still exist in codebase, only removed from active pipeline
