# Implementation Plan: Mejoras Visuales — HUD y Overlays

**Document:** `knowledge/04_mejoras_visuales_hud.md`  
**Date:** 2026-05-01  
**Complexity:** M (3 independent improvements across 5 existing files + 1 new file)

---

## Feature: Visual HUD & Overlay Improvements for Basketball Analysis

### Summary
Replace fragmented visual HUD with unified bottom-bar design (3 sections: Team 1 stats | Ball Control bar | Team 2 stats). Move tactical view from top-left to top-right to avoid overlapping real-game scoreboard overlays. Improve team color contrast for readability (bone-white → steel-blue; dark-red → vivid-red). Adds ball possession as visual split bar instead of text-only percentages. Impact: broadcast-quality visual layout, better information density, professional appearance for MVP.

---

## Definition of Ready (DoR) — pre-flight check

- [x] KB doc is complete with no open questions blocking implementation
- [x] Dependency: `video_1.mp4` test video available — DONE (referenced in KB doc)
- [x] Current drawer architecture understood (8 independent drawer classes in pipeline)
- [x] Team color assignment in `PlayerTracksDrawer` and `TacticalViewDrawer` identified
- [x] `TeamBallControlDrawer` and `PassInterceptionDrawer` implementation reviewed
- [x] `drawers/utils.py` color contrast logic location confirmed
- [x] No external library additions required (OpenCV only)

---

## Files to modify

| File | Change type | What changes |
|------|-------------|--------------|
| `drawers/player_tracks_drawer.py` | Modify (line 12) | Update team color defaults: Team1 `(220, 100, 40)` (BGR blue-steel), Team2 `(40, 40, 200)` (BGR vivid-red) |
| `drawers/tactical_view_drawer.py` | Modify (lines 4, 10–20) | Add `position='top-right'` param to `__init__`, calculate `start_x` dynamically in `draw()` based on frame width and tactical view dimensions |
| `drawers/utils.py` | Modify (lines 86–94) | Add dynamic text color calculation in `draw_ellipse()` using luminance formula: `luminance = 0.299*r + 0.587*g + 0.114*b`, use black text if luminance > 128, else white |
| `drawers/__init__.py` | Modify (add export) | Add `from .stats_hud_drawer import StatsHudDrawer` after line 8 |
| `main.py` | Modify (lines 227–237, 135–160) | Replace `TeamBallControlDrawer` and `PassInterceptionDrawer` in drawers tuple; update `_drawing_pass()` call chain |

---

## Files to create

| File | Purpose |
|------|---------|
| `drawers/stats_hud_drawer.py` | New unified HUD drawer class combining team stats + ball control bar into single bottom-strip overlay |

---

## Execution order

### Phase 1: Team Color Contrast (Mejora 4) — Low-risk baseline
**Estimated: 15 min**

1. **Modify `drawers/player_tracks_drawer.py` line 12**
   - Change `team_1_color=[255, 245, 238]` → `team_1_color=[40, 100, 220]` (BGR: steel-blue)
   - Change `team_2_color=[128, 0, 0]` → `team_2_color=[0, 50, 220]` (BGR: vivid-red)
   - **Rationale:** Improves badge readability immediately on all player tracks
   - **Test:** Run `python main.py input_videos/video_1.mp4 --output_video /tmp/test_colors.mp4 && ffplay /tmp/test_colors.mp4` — observe player ID badges are now blue/red and visible against court background

2. **Modify `drawers/tactical_view_drawer.py` line 4**
   - Same color defaults as above (copy `team_1_color`, `team_2_color` params from `PlayerTracksDrawer`)
   - **Rationale:** Unify color scheme across both drawer classes
   - **Test:** Visual check: tactical view circles now match player badge colors

3. **Modify `drawers/utils.py` lines 86–94** — Add dynamic text color in `draw_ellipse()`
   - **Change:** Replace hardcoded `(0,0,0)` text color with conditional logic:
     ```python
     # At line 86, replace the cv2.putText call:
     # OLD: cv2.putText(frame, f"{track_id}", (int(x1_text),int(y1_rect+15)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,0), 2)
     # NEW:
     r, g, b = color[2], color[1], color[0]  # BGR → RGB
     luminance = 0.299*r + 0.587*g + 0.114*b
     text_color = (0, 0, 0) if luminance > 128 else (255, 255, 255)
     cv2.putText(frame, f"{track_id}", (int(x1_text),int(y1_rect+15)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, text_color, 2)
     ```
   - **Rationale:** With new blue/red colors, ensure track ID text remains legible (black on light backgrounds, white on dark)
   - **Test:** Verify badges are readable in both team colors

---

### Phase 2: Tactical View Repositioning (Mejora 3) — Medium-risk but isolated
**Estimated: 20 min**

1. **Modify `drawers/tactical_view_drawer.py` `__init__()` signature (lines 4–8)**
   - Add parameter: `position='top-right'` after `team_2_color`
   - Store: `self.position = position`
   - Keep `self.start_y = 20` (static)
   - Keep `self.start_x` declaration but now computed in `draw()` (do NOT set in `__init__`)
   - **Rationale:** Allows runtime position selection without breaking backward compatibility
   
2. **Modify `drawers/tactical_view_drawer.py` `draw()` method (lines 10–50)**
   - Add at line 21 (after line 20, before `court_image = cv2.imread(...)`):
     ```python
     frame_h, frame_w = video_frames[0].shape[:2]
     if self.position == 'top-right':
         self.start_x = frame_w - self.width - 20
     else:
         self.start_x = 20
     ```
   - **Rationale:** Compute `start_x` once per draw batch based on actual frame dimensions and tactical view width
   - **Dependencies:** `self.width` is passed as parameter named `width` at line 13 — store it in `__init__` for use in `draw()`
   - **Issue to fix:** `self.width` and `self.height` need to be stored from init or passed. Check signature: `draw()` receives `width` and `height` as params → store them.
   
3. **Update `drawers/tactical_view_drawer.py` `__init__()` to store dimensions**
   - Add `self.width = None` and `self.height = None` to `__init__`
   - OR: Store them from first call to `draw()` (lazy init)
   - **Simpler approach (recommended):** Extract from `draw()` signature — it receives `width` and `height`. Use them locally instead of storing.
   - **Revised logic in `draw()`:**
     ```python
     frame_h, frame_w = video_frames[0].shape[:2]
     tactical_width = width  # parameter already received
     if self.position == 'top-right':
         self.start_x = frame_w - tactical_width - 20
     else:
         self.start_x = 20
     ```
   - **Test:** Run video, verify tactical view appears in top-right corner without clipping, and no longer covers left-side scoreboard area

4. **Update `main.py` line 234** — No changes needed if `TacticalViewDrawer()` defaults to `position='top-right'`
   - **Note:** KB doc specifies `position='top-right'` as default, so instantiation in main.py remains unchanged

---

### Phase 3: Unified HUD + Ball Control Bar (Mejora 1 + 2) — Highest complexity, parallel work possible
**Estimated: 90–120 min**

#### Step A: Create `drawers/stats_hud_drawer.py` (new file)

1. **Create file** at `/Users/germanevangelisti/basketball_analysis/drawers/stats_hud_drawer.py`

2. **Implement `StatsHudDrawer` class** with constructor:
   ```python
   def __init__(self, team_1_color=[40, 100, 220], team_2_color=[0, 50, 220],
                team_1_name="Team 1", team_2_name="Team 2"):
       self.team_1_color = team_1_color
       self.team_2_color = team_2_color
       self.team_1_name = team_1_name
       self.team_2_name = team_2_name
   ```
   - Use new default colors (from Phase 1)
   - Allow custom team names for future internationalization

3. **Implement `draw()` method** matching signature of old drawers:
   ```python
   def draw(self, video_frames, player_assignment, ball_acquisition, passes, interceptions):
       # Returns list of frames with unified HUD
       # Same pattern as existing drawers: enumerate frames, skip frame 0, accumulate output
   ```
   - **Input contract:**
     - `video_frames`: list of frame arrays
     - `player_assignment`: list of dicts (player_id → team)
     - `ball_acquisition`: list of player IDs (who has ball per frame)
     - `passes`: list of ints (1/2 for team, 0 for no pass)
     - `interceptions`: list of ints (1/2 for team, 0 for no interception)
   - **Output:** list of frames (skip frame 0, same as old drawers)

4. **Implement `_draw_frame()` private method**
   - **Parameters:** `frame`, `frame_num`, `player_assignment`, `ball_acquisition`, `passes`, `interceptions`
   - **Draw order:**
     a. **HUD background:** Semi-transparent dark rectangle y=78%–96% of frame
     b. **Vertical separators:** Thin lines at x=33% and x=66%
     c. **Left section (Team 1, x=1%–33%):** Team name (color, bold), stats row (Passes/Intercept counts)
     d. **Center section (x=33%–66%):** Ball control split bar with label
     e. **Right section (x=66%–100%):** Team 2 name (color, bold, right-aligned), stats row

5. **Implement `_draw_possession_bar()` private method** (called from `_draw_frame()`)
   - **Input:** `frame`, `frame_num`, `player_assignment`, `ball_acquisition`, `team_1_pct`, `team_2_pct`
   - **Logic:**
     ```python
     # Calculate cumulative possession up to this frame
     ball_control = self._get_team_ball_control(player_assignment[:frame_num+1], 
                                                ball_acquisition[:frame_num+1])
     team_1_pct = (ball_control == 1).sum() / len(ball_control) if len(ball_control) > 0 else 0
     team_2_pct = (ball_control == 2).sum() / len(ball_control) if len(ball_control) > 0 else 0
     ```
   - **Bar dimensions:**
     - x range: center third, 10%–90% width (80% of third)
     - height: 12px
     - vertically centered in HUD
   - **Draw:**
     - Filled rectangle Team 1 color from bar_x1 to split_x
     - Filled rectangle Team 2 color from split_x to bar_x2
     - Border: thin gray outline
     - Label "Ball Control" above bar
     - Percentage labels below (Team 1 left, Team 2 right)
   - **Edge case:** If no ball control yet (all frames with ball_acquisition=-1), draw gray bar with "–"

6. **Implement `_get_team_ball_control()` private method**
   - **Copy logic from `TeamBallControlDrawer.get_team_ball_control()`** (lines 11–39 of current drawer)
   - Returns numpy array of team IDs (1/2/-1) per frame

#### Step B: Update `drawers/__init__.py` (line 9)

1. **Add import:** `from .stats_hud_drawer import StatsHudDrawer`
2. **Update export line 8:** Add `StatsHudDrawer` to file (no need to remove old classes yet, but they'll be unused)

#### Step C: Modify `main.py` (lines 227–237, 132–160)

1. **Update drawers tuple** (lines 227–237)
   - **Replace:**
     ```python
     TeamBallControlDrawer(),
     FrameNumberDrawer(),
     PassInterceptionDrawer(),
     ```
   - **With:**
     ```python
     FrameNumberDrawer(),
     StatsHudDrawer(),
     ```
   - **Result:** Tuple goes from 8 to 7 drawers (combine 2 into 1)

2. **Update `_drawing_pass()` unpacking** (line 135–137)
   - **Old:**
     ```python
     (player_tracks_drawer, ball_tracks_drawer, court_keypoint_drawer,
      team_ball_control_drawer, frame_number_drawer, pass_interceptions_drawer,
      tactical_view_drawer, speed_and_distance_drawer) = drawers
     ```
   - **New:**
     ```python
     (player_tracks_drawer, ball_tracks_drawer, court_keypoint_drawer,
      frame_number_drawer, stats_hud_drawer,
      tactical_view_drawer, speed_and_distance_drawer) = drawers
     ```

3. **Update drawing call chain** (lines 146–160)
   - **Replace lines 152–157** (old team_ball_control and pass_interceptions calls) with single call:
     ```python
     out = stats_hud_drawer.draw(
         out, player_assignment[s], results['ball_acquisition'][s],
         results['passes'][s], results['interceptions'][s]
     )
     ```
   - **Remove these old lines:**
     ```
     out = team_ball_control_drawer.draw(
         out, player_assignment[s], results['ball_acquisition'][s]
     )
     out = pass_interceptions_drawer.draw(
         out, results['passes'][s], results['interceptions'][s]
     )
     ```
   - **Result:** Call chain flows: player → ball → court → frame_number → stats_hud → speed_distance → tactical_view

4. **Update imports** (line 16–25)
   - **Add:** `StatsHudDrawer` to import line
   - **Remove:** `TeamBallControlDrawer` and `PassInterceptionDrawer` from imports (optional, won't hurt if left)

---

## Key risks & mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **Frame 0 skipping logic** — Old drawers skip frame 0; new `StatsHudDrawer` must match | Medium: Output frame count mismatch if not consistent | Implement `_draw_frame()` to skip frame 0 in enumerate loop (copy pattern from `PassInterceptionDrawer.draw()` lines 60–66) |
| **Tactical view width/height not available in init** — `__init__()` doesn't receive dimensions | High: `start_x` calculation fails if width undefined | Use `width` parameter from `draw()` method signature; compute `start_x` inside `draw()` before first use (lines 20–26) |
| **Unbalanced HUD layout if percentages are extreme** — e.g., 99%/1% split bar looks off | Low: Visual but not data-critical | Bar width calculation is inherently proportional; no mitigation needed |
| **Test video too short (4 sec, 117 frames)** — Passes/interceptions will still be 0 | Low: Expected per KB doc; not a code bug | Note in test plan: use longer video for validating stats accumulation |
| **Color default breakage** — If other code reads hardcoded colors from main | Low: All color init happens in drawer constructors | Search codebase for hardcoded `[255, 245, 238]` or `[128, 0, 0]` — none found except drawers |

---

## Definition of Done (DoD)

All items must be verifiable by running a command or inspecting output.

- [ ] **Phase 1 (Colors) complete:**
  - [ ] `drawers/player_tracks_drawer.py:12` shows `team_1_color=[40, 100, 220]` and `team_2_color=[0, 50, 220]`
  - [ ] `drawers/tactical_view_drawer.py:4` shows same color defaults
  - [ ] `drawers/utils.py:86–94` includes luminance calculation and conditional text color
  - [ ] Run `python main.py input_videos/video_1.mp4 --output_video /tmp/phase1.mp4` completes without error
  - [ ] Visual inspection: player ID badges are blue (Team 1) and red (Team 2) in output video

- [ ] **Phase 2 (Tactical View) complete:**
  - [ ] `drawers/tactical_view_drawer.py` has `position='top-right'` param in `__init__`
  - [ ] `draw()` method computes `start_x = frame_w - tactical_width - 20` when `position=='top-right'`
  - [ ] Run pipeline, verify tactical view appears in top-right corner of output
  - [ ] Verify tactical view does not overlap left side of frame (where real game scoreboard typically is)

- [ ] **Phase 3 (Unified HUD) complete:**
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

- [ ] **Cross-phase integration:**
  - [ ] Run full pipeline with all 3 phases: `python main.py input_videos/video_1.mp4 --output_video output_videos/test_hud_final.mp4`
  - [ ] Verify: player badges (new colors) + tactical view (top-right) + unified HUD (bottom bar) all visible and non-overlapping
  - [ ] Frame count matches input (117 frames for video_1.mp4)
  - [ ] No exceptions in logs

- [ ] **Existing tests pass:**
  - [ ] Run `python -m pytest tests/ -v`
  - [ ] All 8 existing tests pass (no regressions in ball_acquisition, bbox_utils, etc.)

- [ ] **New unit tests for StatsHudDrawer:**
  - [ ] `tests/test_stats_hud_drawer.py` created
  - [ ] Test: `test_draw_returns_correct_frame_count()` — input 100 frames, expect 99 output (skips frame 0)
  - [ ] Test: `test_possession_bar_calculation()` — mock data with known possession split, verify bar proportions
  - [ ] Test: `test_edge_case_no_possession_data()` — all frames with `ball_acquisition=-1`, verify gray bar with "–" rendered
  - [ ] Test: `test_dynamic_text_color_contrast()` — verify luminance logic produces readable text on both team colors

- [ ] **No regressions in pipeline:**
  - [ ] Stub caching still works (delete stubs, re-run, verify stubs regenerated)
  - [ ] Chunk-boundary safety: ByteTrack state persists across chunks (player IDs continuous)
  - [ ] Global frame numbering correct (FrameNumberDrawer shows frame 1–117 for test video)

- [ ] **Implementation log updated:**
  - [ ] `knowledge/implementation/04-mejoras-visuales-hud/implementation_log.md` created and timestamped with Phase 1, 2, 3 completion notes

---

## Estimated complexity

**M (Medium)** — 90–150 min

**Justification:**
- **Phase 1 (Colors):** Trivial — 3 simple line changes across 2 files + 1 method patch in utils
- **Phase 2 (Tactical View):** Low-medium — Requires understanding of dynamic positioning but minimal logic (~10 lines added)
- **Phase 3 (Unified HUD):** Medium-high — New class with 200+ LOC, complex layout logic, coordinate calculations. However, logic is straightforward (mostly direct from KB doc). Moderate risk of layout arithmetic errors.
- **Integration & Testing:** Low-medium — Mostly visual verification; no complex dependencies

**Not S because:** Not trivial coordinate/dimension changes, requires new class creation.  
**Not L because:** No major architectural changes, no new ML models, no refactoring of existing pipeline cores.

---

## Recommended agent

**cv-engineer** (or full-stack if unavailable)

**Justification:**
- Heavy visual/layout expertise required (HUD positioning, color contrast, coordinate math)
- Knowledge of OpenCV drawing primitives essential (cv2.rectangle, cv2.putText, alpha blending)
- Must understand frame dimensions, aspect ratios, percentage-based layouts
- Testing requires visual inspection of output video
- No backend logic or database changes; pure rendering

---

## Testing strategy per phase

### Phase 1 (Colors)
```bash
# Clear stubs to force re-run (colors affect visualization only, not detection)
rm -rf stubs/*.pkl

# Run pipeline
python main.py input_videos/video_1.mp4 --output_video /tmp/test_phase1.mp4

# Visual check: Open in any player
# Expected: Blue player ID badges (Team 1), red badges (Team 2)
# Expected: Text is readable (black on light blue, white on dark red due to contrast logic)
```

### Phase 2 (Tactical View)
```bash
# No need to clear stubs (tactical view is drawing-only)
python main.py input_videos/video_1.mp4 --output_video /tmp/test_phase2.mp4

# Visual check:
# Expected: Tactical view appears in top-right corner
# Expected: No clipping of tactical view off right edge
# Expected: Left side of frame (y=0-100px, x=0-200px) remains clear
```

### Phase 3 (Unified HUD)
```bash
# Clear stubs not necessary (stats drawer uses existing data)
python main.py input_videos/video_1.mp4 --output_video /tmp/test_phase3.mp4

# Visual check (frame 60–70 are good snapshots for visual inspection):
ffplay /tmp/test_phase3.mp4

# Expected: Bottom bar (y~560–690 in 720p, full width)
# Expected: Left third shows "Team 1" (blue text) + "Passes: 0 | Intercept: 0"
# Expected: Center third shows "Ball Control" label + colored split bar + percentages
# Expected: Right third shows "Team 2" (red text, right-aligned) + stats
# Expected: Thin gray separators at x~427 and x~853 (33% and 66% of 1280px width)
```

### Integration Test
```bash
# Run all three phases together
python main.py input_videos/video_1.mp4 --output_video output_videos/test_hud_final.mp4

# Frame count verification
ffprobe -v error -select_streams v:0 -count_frames -show_entries stream=nb_read_frames \
  -of csv=p=0 output_videos/test_hud_final.mp4
# Should output: 117 (same as input video)

# Pytest (catch regressions)
python -m pytest tests/test_stats_hud_drawer.py -v
python -m pytest tests/ -v
```

---

## Implementation notes

### Architecture preservation
- **Chunk pipeline invariant:** Each drawer's `draw()` method operates on chunk_frames (200-frame windows). `StatsHudDrawer` must accumulate stats up to current frame number (not just within chunk) — use `player_assignment[s]` and `results['ball_acquisition'][s]` slices as provided by `_drawing_pass()`.
- **Frame 0 handling:** All drawers skip frame 0 (first frame is dummy/warmup). `StatsHudDrawer.draw()` must do the same (enumerate and `if frame_num == 0: continue`).
- **ByteTrack continuity:** No changes; tactical view repositioning doesn't affect player tracking.

### Implementation order recommendation (from KB doc)
Follow exactly: **Mejora 3 → Mejora 4 → Mejora 1+2**

This order is optimal because:
1. Mejora 3 (tactical view move) is lowest-risk, tests repositioning logic early
2. Mejora 4 (colors) is a foundation for Mejora 1+2 (unified HUD uses new colors by default)
3. Mejora 1+2 (HUD) are most complex and can be tested against the now-stable visual foundation

### Deployment path
1. Create feature branch: `feature/04-mejoras-visuales-hud`
2. Commit Phase 1 changes (colors)
3. Commit Phase 2 changes (tactical view)
4. Commit Phase 3 changes (unified HUD)
5. Test entire pipeline with video_1.mp4
6. Create PR with all three phases

---

## Ambiguities & decisions

**Q: Should `StatsHudDrawer` store cumulative stats or recalculate each frame?**
- **Decision:** Recalculate each frame using array slicing (like existing `TeamBallControlDrawer` line 100). Simpler, no state management.

**Q: What if frame dimensions change mid-video?**
- **Decision:** Not applicable; video dimensions are constant. Tactical view calculates `start_x` once per `draw()` call.

**Q: Should passes/interceptions on frame 0 be included in stats?**
- **Decision:** No; frame 0 is skipped like existing drawers. Cumulatively calculated only for frames 1+.

**Q: Backward compatibility for old color parameters?**
- **Decision:** New defaults are used; old hardcoded `[255, 245, 238]` is deprecated. No migration needed (colors only affect rendering, not stored data).

---

## File paths for reference

**Source files (read, modify):**
- `/Users/germanevangelisti/basketball_analysis/main.py` — lines 16–25, 227–237, 132–160
- `/Users/germanevangelisti/basketball_analysis/drawers/__init__.py` — add import
- `/Users/germanevangelisti/basketball_analysis/drawers/player_tracks_drawer.py` — line 12
- `/Users/germanevangelisti/basketball_analysis/drawers/tactical_view_drawer.py` — lines 4–50
- `/Users/germanevangelisti/basketball_analysis/drawers/utils.py` — lines 86–94
- `/Users/germanevangelisti/basketball_analysis/drawers/team_ball_control_drawer.py` — reference only (copy logic to StatsHudDrawer)
- `/Users/germanevangelisti/basketball_analysis/drawers/pass_and_interceptions_drawer.py` — reference only

**New file:**
- `/Users/germanevangelisti/basketball_analysis/drawers/stats_hud_drawer.py` — create

**Test files:**
- `/Users/germanevangelisti/basketball_analysis/tests/test_stats_hud_drawer.py` — create

**Video reference:**
- `input_videos/video_1.mp4` — 117 frames, 30fps, 1280x720px (test file)

---

## Next steps

1. **Pre-implementation review:** cv-engineer reviews this plan, confirms coordinate calculations (HUD bar y=78%–96% = ~560–690px at 720p)
2. **Phase 1 PR:** Commit color changes, get visual review
3. **Phase 2 PR:** Commit tactical view repositioning, verify no clipping
4. **Phase 3 PR:** Commit unified HUD, validate layout and stat accumulation
5. **Integration PR:** Combine all three, final full-pipeline test with longer video if available

---

*End of plan. Ready for implementation with cv-engineer agent.*
