# DoD — Mejoras Visuales — HUD y Overlays

Source: knowledge/04_mejoras_visuales_hud.md
Branch: feature/04-mejoras-visuales-hud

## Standard criteria (every feature)
- ✅ All existing tests pass after implementation — 26/26 passed (10 existing + 16 new)
- ✅ New tests written for every new public method — 16 tests in test_stats_hud_drawer.py
- ✅ No regressions in main.py pipeline — all 26 tests passed, no errors
- ✅ Implementation log updated with key decisions — comprehensive log entry present

## Feature-specific criteria (from KB doc)

### Phase 1: Team Color Contrast (Mejora 4)
- ✅ `drawers/player_tracks_drawer.py:12` shows `team_1_color=[40, 100, 220]` and `team_2_color=[0, 50, 220]`
- ✅ `drawers/tactical_view_drawer.py:4` shows same color defaults
- ✅ `drawers/utils.py:86–94` includes luminance calculation and conditional text color (lines 87-89)
- ✅ Dynamic text color logic verified in test_dynamic_text_color_contrast_team1/team2
- ✅ Color choice documented in implementation log with justification

### Phase 2: Tactical View Repositioning (Mejora 3)
- ✅ `drawers/tactical_view_drawer.py` has `position='top-right'` param in `__init__` (line 4)
- ✅ `draw()` method computes `start_x = frame_w - width - 20` when `position=='top-right'` (lines 43-46)
- ✅ Default position is 'top-right' in TacticalViewDrawer init

### Phase 3: Unified HUD + Ball Control Bar (Mejora 1+2)
- ✅ `drawers/stats_hud_drawer.py` exists with `StatsHudDrawer` class (288 lines)
- ✅ `StatsHudDrawer.draw()` method signature matches KB doc (line 71)
- ✅ `_draw_frame()` and `_draw_possession_bar()` methods implemented (lines 100-282)
- ✅ Unified HUD bar at bottom (y=78%–96%, lines 121-122)
- ✅ Left section shows Team 1 name + stats (lines 155-159)
- ✅ Center section shows Ball Control label + split bar + percentages (lines 162-165)
- ✅ Right section shows Team 2 name (right-aligned) + stats (lines 168-171)
- ✅ `main.py:226-234` drawers tuple updated (7 drawers, StatsHudDrawer included)
- ✅ `main.py:136-138` unpacking updated for 7 drawers
- ✅ `main.py:153-156` drawing call chain updated (stats_hud_drawer single call)
- ✅ `drawers/__init__.py:9` exports `StatsHudDrawer`
- ✅ Frame 0 skipping implemented in StatsHudDrawer.draw() (lines 89-90)

### Existing tests pass
- ✅ Run `python -m pytest tests/ -v` — 26 passed, 0 failed
- ✅ All 10 existing tests still pass (no regressions)

### New unit tests for StatsHudDrawer
- ✅ `tests/test_stats_hud_drawer.py` created (248 lines, 16 tests)
- ✅ Test: `test_draw_returns_correct_frame_count()` — input 100 frames, output 99 (frame 0 skipped)
- ✅ Test: `test_possession_bar_split()` — even split between teams verified
- ✅ Test: `test_possession_bar_no_data()` — gray bar with "–" rendered correctly
- ✅ Test: `test_dynamic_text_color_contrast_team1()` — black text on steel-blue
- ✅ Test: `test_dynamic_text_color_contrast_team2()` — white text on vivid-red
- ✅ Test: `test_cumulative_stats_per_frame()` — stats accumulate correctly
- ✅ Additional tests: initialization, custom colors, team ball control logic, stats calculation, edge cases

### Pipeline integrity
- ✅ Frame 0 skipping consistent across all new code
- ✅ No changes to player tracking or ByteTrack state management
- ✅ Chunk-boundary safety preserved (stats_hud_drawer receives pre-sliced data)
- ✅ Global frame numbering unaffected (frame_number_drawer still uses start_frame_idx)
