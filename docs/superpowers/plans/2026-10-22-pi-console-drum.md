# Pi Console Drum Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Model the ⌀160 × 115 two-part Pi console drum in Fusion 360 as gated, verified scripts, export the five print bodies, and hand the owner renders.

**Architecture:** One new Fusion document built by five stage scripts (`cad/pi_drum_a.py` … `_e.py`) in the style of the pad's `cad/lap_disc_*.py`: named parameters first, every feature asserts its analytic volume change, point containment reads geometry back, the fusionhelper verification block closes each script. A launcher runs bundled artefacts through FusionHelper's MCP client. An art script turns the existing SVG layers into placement-baked DXFs for the wrapped debosses.

**Tech Stack:** Fusion 360 Python API (`adsk.core`, `adsk.fusion`), FusionHelper (`fusionhelper.buildkit`, `bundle`, `preflight`, verify block) run under `uv --python 3.12`, shapely + svgelements + ezdxf + Pillow for the art, pytest for the offline pieces.

**Spec:** `docs/superpowers/specs/2026-10-21-pi-console-drum-design.md`

## Global Constraints

- The fusion-design skill's ten rules apply to every stage script: `createByString` only (R1), every dimension bound to a parameter (R2), no topology by index (R4), no held BRep across a parameter write (R5), sketch-to-model mapping derived at runtime (R6), `snake_case` parameters (R7), the verify stub appended by the bundler (R8), no exception handling (R9), no saves (R10).
- Toolchain, verbatim from `.claude/skills/fusion-design/VENDORED.md`:
  `uv run --no-project --python 3.12 --with-editable C:/Users/gethi/sources/FusionHelper python -m fusionhelper.bundle cad/<script>.py`
  then `… python -m fusionhelper.preflight cad/<script>.bundled.py`, exit code checked explicitly, never through a pipe. The gate's *stub fingerprint drifted* line is a warning from FusionHelper's lock, not a finding against the script.
- Execution: `python cad/fusion_run.py cad/<script>.bundled.py` (Task 1). Hard cap five executes per stage; third attempt is a regeneration.
- Every stage script starts with `FH_ATTEMPT`, `FH_OPTS` (with `only_params` listing that stage's root parameters and `max_bodies`), `INTERFERENCE_ALLOWED = []`, `CLEARANCES = []`, `EXPECT_DEAD = []`, then `from fusionhelper.buildkit import *`, and checks `app.activeDocument.name.startswith("Pi Console Drum")` before touching anything.
- Model frame and every number: the spec's section 3 parameter table. Units mm in parameters, cm in API calls (`MM = 0.1`).
- Document: the owner creates a new Fusion design named **Pi Console Drum** and saves it once before Task 3 runs (R10a).
- Commits on `main` after each green stage; the bundled artefact is committed beside its author script, as the pad stages are.
- No time estimates anywhere in this plan.

## Review Focus

1. **Negative position expressions.** Four of the six button centres and two column centres have negative x or y. A distance dimension is unsigned; a negative expression slides the feature to its mirror. Task 5 reads every hole centre back by containment at the signed coordinate, not at its absolute value.
2. **Circular pattern direction and count.** Pattern direction sign is unreliable and `body.volume` is a bad oracle for small holes. Tasks 3 and 5 validate every pattern by face-count delta and by containment at the last instance's expected angle.
3. **Columns attached, not floating.** The column cylinder at r 72.8 ± 4 clears the cup wall at r 77 by 0.2. Only the web joins it. Task 5 asserts the cup is one body after the joins and that a point inside the web at r 77.2 is solid.
4. **Deboss face selection after the groove and chamfers.** The exhaust groove and the joint chamfer split the cup's outer cylinder into several faces. Task 6 selects the r 80 face whose z range contains z 35–99 and asserts exactly one match before embossing.
5. **The art pocket on the bed face.** The lid prints face down, so the pocket is the first three layers. Task 5 asserts the pocket floor is a single planar face at z 114.4 with area 50.1 × 68.4, and that no button hole breaks into it (containment at the pocket's four corners is solid at z 114.6 and empty at z 114.2).

---

### Task 1: Launcher and toolchain record

**Files:**
- Create: `cad/fusion_run.py`
- Create: `cad/tests/test_fusion_run.py`
- Modify: `.claude/skills/fusion-design/VENDORED.md` (the "Fusion MCP server" paragraph)

**Interfaces:**
- Consumes: `McpClient(url).initialize()`, `.execute(script_text) -> ExecResult(success, message, error)` from `C:/Users/gethi/sources/FusionHelper/tests/integration/mcp_client.py` (import by inserting that directory into `sys.path`).
- Produces: `verdict_from(stdout: str) -> dict | None` (the parsed last `FH_VERDICT1 {…}` line); `main(argv: list[str]) -> int` returning 0 on `verdict["status"] == "pass"`, 2 on any other verdict, 3 when the script failed or no verdict line was printed. Prints the script's stdout (and error text) in full before the exit line. Env `FUSION_MCP_URL` overrides `http://127.0.0.1:27182/mcp`.

**Confidence:** 95%. The client and the envelope were exercised twice today in spikes.

- [ ] **Step 1: Write the failing tests**

```python
def test_verdict_from_takes_last_verdict_line():
    s = 'FH_CHECK1 {"a":1}\nFH_VERDICT1 {"status":"fail"}\nnoise\nFH_VERDICT1 {"status":"pass"}\n'
    assert verdict_from(s) == {"status": "pass"}

def test_verdict_from_none_without_line():
    assert verdict_from("hello\n") is None

def test_main_exit_codes(monkeypatch, tmp_path):
    # monkeypatch fusion_run.McpClient with a stub whose execute returns
    # ExecResult(True, 'FH_VERDICT1 {"status":"pass"}', '') -> 0;
    # status "fail" -> 2; ExecResult(False, '', 'Traceback') -> 3
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run --no-project --python 3.12 --with pytest python -m pytest cad/tests/test_fusion_run.py -v`
Expected: FAIL, `cad.fusion_run` not importable.

- [ ] **Step 3: Implement `cad/fusion_run.py`**

`verdict_from`, `main`, and `if __name__ == "__main__": sys.exit(main(sys.argv[1:]))`. The script file is read as UTF-8; `FH_MCP_TIMEOUT_S` is left to the client's default.

- [ ] **Step 4: Run the tests to verify they pass**

Run: the same command. Expected: 3 passed.

- [ ] **Step 5: Live check against Fusion**

Run: `python cad/fusion_run.py cad/lap_disc_o.bundled.py` is **not** safe (it edits the pad document). Instead run the launcher on a one-line script file containing `def run(_c): print("FH_VERDICT1 {\"status\": \"pass\"}")` saved in the scratchpad. Expected: exit 0 and the line echoed.

- [ ] **Step 6: Record the launcher in VENDORED.md**

Replace the sentence "scripts go through FusionHelper's stdlib client (`tests/integration/mcp_client.py`, `McpClient.execute`)" with the `python cad/fusion_run.py <bundled>` command and its exit codes.

- [ ] **Step 7: Commit**

```bash
git add cad/fusion_run.py cad/tests/test_fusion_run.py .claude/skills/fusion-design/VENDORED.md
git commit -m "Launcher: run bundled Fusion scripts through FusionHelper's MCP client"
```

---

### Task 2: Art preparation script

**Files:**
- Create: `cad/art/drum_art.py`
- Create: `cad/art/tests/test_drum_art.py`
- Create (outputs, committed): `cad/art/drum/chunli_sil.dxf`, `cad/art/drum/chunli_sil.png`, `cad/art/drum/sf2_solid_art.dxf`, `cad/art/drum/sf2_holes_art.dxf`

**Interfaces:**
- Consumes: `cad/art/layers/all/*.svg` (viewBox 2160 × 2592, `ART_H_MM = 64` in `split_layers.py`), `cad/art/logo/sf2_deboss_solid.dxf` and `sf2_deboss_holes.dxf` (pad placement baked in: solid x −58.500..58.479, y 43.000..102.777).
- Produces, as a CLI run under `uv run --no-project --python 3.12 --with shapely --with svgelements --with ezdxf --with pillow python cad/art/drum_art.py …`:
  - `silhouette <svg_dir> <out.dxf> --height H` : union of every closed path in every SVG in the directory, outer boundaries only (holes dropped), scaled so the bbox height is H mm, centred on (0, 0), y up; writes closed LWPOLYLINEs and a PNG preview beside it.
  - `art <in.dxf> <out.dxf>` : re-centres a DXF's bbox on (0, 0), no scale.
  - `place <in.dxf> <out.dxf> --cx CX --cy CY [--flip-y]` : optional mirror about the x axis, then translate the bbox centre to (CX, CY). Stage D uses this after the mapping probe.
  - Each command prints `bbox: xmin xmax ymin ymax` on its last line.
- Library functions with the same names (`silhouette(paths, height) -> shapely.Polygon|MultiPolygon`, `transform(entities, cx, cy, flip_y)`), tested directly.

**Confidence:** 92%. Libraries resolve under uv (checked today; cairosvg does not, so no cairo). The remaining doubt is whether the eleven layer SVGs union to one polygon or several islands (the hair bun is a separate shape); the test accepts a MultiPolygon and the preview shows the owner what they get.

- [ ] **Step 1: Write the failing tests**

```python
def test_silhouette_unions_two_overlapping_squares_and_drops_holes(tmp_path):
    # two SVG files: a 100x100 square at (0,0) and a 100x100 square at (50,50),
    # the second with a 20x20 inner hole; silhouette(..., height=59) has
    # bbox height 59.0 ± 0.01, width 59.0, area == 59*59*0.75 ± 0.5, no interiors

def test_place_flip_and_centre(tmp_path):
    # an input DXF with one polyline bbox x 0..10, y 0..20; place --cx 5 --cy -67 --flip-y
    # output bbox is x 0..10, y -77..-57 and the vertex that was at y=20 is now at y=-77

def test_art_recentres_logo_sized_box(tmp_path):
    # input bbox x -58.5..58.479, y 43..102.777 -> output bbox centred on (0,0), size unchanged ± 1e-6
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run --no-project --python 3.12 --with shapely --with svgelements --with ezdxf --with pillow --with pytest python -m pytest cad/art/tests -v`
Expected: FAIL, module missing.

- [ ] **Step 3: Implement `cad/art/drum_art.py`**

SVG parsing as `split_layers.py` does (svgelements `SVG.parse`, `Path` segments to shapely polygons via `polygonize`/`unary_union`); DXF read and write with ezdxf (`modelspace().query("LWPOLYLINE")`); preview with Pillow `ImageDraw.polygon` at 4 px/mm.

- [ ] **Step 4: Run the tests to verify they pass**

Expected: 3 passed.

- [ ] **Step 5: Produce the art-space files**

Run the three commands: `silhouette cad/art/layers/all cad/art/drum/chunli_sil.dxf --height 59`, `art cad/art/logo/sf2_deboss_solid.dxf cad/art/drum/sf2_solid_art.dxf`, `art cad/art/logo/sf2_deboss_holes.dxf cad/art/drum/sf2_holes_art.dxf`.
Expected last lines: silhouette bbox height 59.00, width 42 ± 1 (the art's 0.714 aspect; if the width is outside 40–44 the aspect assumption in the spec is wrong and the spec's `sil_w` is updated to the measured value); logo bbox x −58.49..58.49, y −29.89..29.89.

- [ ] **Step 6: Commit**

```bash
git add cad/art/drum_art.py cad/art/tests cad/art/drum
git commit -m "Drum art: silhouette union and DXF placement script, art-space files"
```

---

### Task 3: Stage A, the base

**Files:**
- Create: `cad/pi_drum_a.py` (and its committed `cad/pi_drum_a.bundled.py`)

**Interfaces:**
- Consumes: the owner's saved document **Pi Console Drum**; `cad/fusion_run.py`.
- Produces: user parameters from the spec table for the base (`drum_d`, `wall_t`, `drum_h`, `split_z`, `floor_t`, `col_r`, `col_d`, `col_foot_z`, `pi_hole_px`, `pi_hole_py`, `pi_boss_d`, `pi_boss_h`, `pi_insert_hole`, `chan_n`, `chan_w`, `chan_d`, `chan_r0`, `intake_n = 2 * chan_n`, `intake_d`, `intake_r1`, `intake_r2`, `screw_clear_d`, `csk_d`, `joint_chamfer`, plus derived `drum_r = drum_d / 2`, `cavity_r = drum_r - wall_t`); one body named **base**; construction planes `floor_top` (z = `floor_t`) and `split` (z = `split_z`); features named `base_floor`, `base_wall`, `floor_channel`, `floor_channel_pattern`, `intake_holes`, `pi_boss`, `pi_insert`, `base_screw`.

**Confidence:** 90%. Every operation has a pad precedent except the circular pattern and the countersink hole feature, both standard API with the kit's validation rules.

- [ ] **Step 1: Write `cad/pi_drum_a.py`**

Build order and oracles, each `check_delta` against the analytic value computed from `ctx.val(...)`:
1. `ensure_params` as in `cad/lap_disc_o.py`.
2. Floor: sketch on XY, `bound_circle` ⌀`drum_d`, extrude `floor_t` new body → `base`. Oracle: π·r²·t.
3. Wall: sketch on `floor_top`, two bound circles ⌀`drum_d` and 2·`cavity_r`, ring profile by area, extrude `split_z - floor_t` join. Oracle: π(r_o² − r_i²)·h.
4. Floor channels: on the floor's underside (sketch on XY, cut upward from z 0), one rectangle `chan_w` wide from r `chan_r0` to r `drum_r + 1 mm` along the +x axis (`bound_rect2`, x from `chan_r0` to `drum_r + 1 mm`, y centred on 0), `blind_cut` `chan_d` upward; then `circularPatternFeatures` about the Z axis, quantity `chan_n`, `patternComputeOption = AdjustPatternCompute`. Oracle: face-count delta ≥ 3·(n − 1); volume delta within 2 % of n·w·d·(r_o − r0); containment empty at (r 65, z 1) on the last instance's angle and solid at (r 65, z 2.5).
5. Intake holes: one sketch on XY, `intake_n` = 2·`chan_n` circles via `bound_circle`, two per channel angle at `intake_r1` and `intake_r2` (`x_pos = "intake_r1 * cos(i * 360 deg / chan_n)"`, `v_pos` with sin, and the same for `intake_r2`), each seeded with a +0.1·i mm jitter; one `through_cut`. Oracle: n·π·(d/2)²·(`floor_t` − `chan_d`), since each hole opens into a channel; face-count delta ≥ n.
6. Pi bosses: sketch on `floor_top`, four circles at (±`pi_hole_px`/2, ±`pi_hole_py`/2) with signed expressions, extrude `pi_boss_h` join. Oracle: 4·π·(d/2)²·h. Then `pi_insert` circles ⌀`pi_insert_hole` blind cut 4 mm from the boss tops. Containment: empty at each boss centre z 6; solid at r 2.5 from it.
7. Base screw holes: `holeFeatures.createCountersinkInput(screw_clear_d, csk_d, "90 deg")` at four sketch points on the floor's underside at `col_r` on ±20°, ±160°, through all. Oracle: volume delta = 4·(cylinder + frustum) from the parameters, 1 % tolerance.
8. Read-back: containment at every hole; `base` is one body; print bbox and volume.

- [ ] **Step 2: Bundle and gate**

Run the bundle command, then the preflight command; check `$?` is 0. Fix findings by rule number; three preflight fixes maximum.

- [ ] **Step 3: Execute**

Run: `python cad/fusion_run.py cad/pi_drum_a.bundled.py`
Expected: exit 0; `FH_VERDICT1` status pass; the script's own `done` line with the base volume (about 104.4 cm³ before holes, about 103.9 after).

- [ ] **Step 4: Render for the owner**

In the same session, `app.activeViewport.saveAsImageFile` is R10-safe; add a final block to the script that writes `cad/renders/pi_drum_stageA_iso.png` and `_top.png` (1600 × 1200) after the verdict-independent build. Expected: two PNGs.

- [ ] **Step 5: Commit**

```bash
git add cad/pi_drum_a.py cad/pi_drum_a.bundled.py cad/renders/pi_drum_stageA_*.png
git commit -m "Stage A: the drum base (D-021)"
```

---

### Task 4: Stage B, socket pads

**Files:**
- Create: `cad/pi_drum_b.py` (+ bundled)

**Interfaces:**
- Consumes: body `base`, plane `floor_top`, parameters from Task 3.
- Produces: parameters `pad_w`, `pad_back_t`, `pad_z0`, `pad_z1`, `pad_r = sqrt(drum_r^2 - (pad_w/2)^2)` (the chord plane distance, 78.58), four angle parameters `pad_ang_1..4` = 45, 75, 105, 135 deg, and per socket `hdmi_cut_w`, `hdmi_cut_h`, `hdmi_screw_pitch` (placeholders 20 × 12, 28), `usbc_cut_w/h/screw_pitch` (10 × 5, 18), `usba_cut_w/h/screw_pitch` (14 × 16, 28), `rj45_cut_w/h/screw_pitch` (16 × 14, 28); features `pad_<n>_flat`, `pad_<n>_back`, `pad_<n>_cut`, `pad_<n>_pilots`. Pads in angle order RJ45, USB-C, HDMI, USB-A.

**Confidence:** 90%. The placeholder values are the only uncertainty and are parameters by design (OI-013); the geometry is four repeats of stage O's radial-plane recipe.

- [ ] **Step 1: Write `cad/pi_drum_b.py`**

For each pad: a construction plane `setByAngle` about the Z axis at `pad_ang_n` (probe its mapping as `radial_plane_checked` does), a second plane offset from it by `pad_r` (the chord plane), sketch on the chord plane: rectangle `pad_w` × (`pad_z1 - pad_z0`) centred at z `(pad_z0 + pad_z1)/2`; `blind_cut` outward `drum_r - pad_r + 1 mm` → the flat. Oracle: the circular-segment area × height, computed in-script from `drum_r` and `pad_w`. Then a rectangle `pad_w + 4` × (`pad_z1 - pad_z0 + 2`) on the same plane extruded inward `pad_back_t` join → the thickening; oracle: its box volume minus the part already inside the wall (segment between r 73.58 and 77). Then the socket cutout `*_cut_w × *_cut_h` through-cut at the pad centre and two ⌀2.5 pilots at ±`*_screw_pitch/2` blind 6 mm.
Read-back: the pad floor is planar at distance `pad_r` from the axis (`flat_faces_at`-style predicate on the plane's normal); solid at r 75 behind the pad centre (thickening present), empty inside each cutout.

- [ ] **Step 2: Bundle, gate, execute** as Task 3 steps 2–3. Expected: pass; base volume drops by the four flats and cutouts and rises by the four thickenings, each asserted.

- [ ] **Step 3: Render** `cad/renders/pi_drum_stageB_rear.png` (camera from +y).

- [ ] **Step 4: Commit** `"Stage B: socket pads with placeholder cutouts (OI-013)"`.

---

### Task 5: Stage C, the cup

**Files:**
- Create: `cad/pi_drum_c.py` (+ bundled)

**Interfaces:**
- Consumes: parameters and planes from Task 3.
- Produces: parameters `lid_t`, `fit_clear`, `col_clear`, `btn_hole`, `btn_ring_r`, `btn_arc_pitch`, `btn_ang_p1..p4` (= −151.5, −110.5, −69.5, −28.5 deg, derived from `btn_arc_pitch` as `-90 deg - 1.5 * btn_arc_pitch` …), `btn_ang_sel = 160 deg`, `btn_ang_hk = 20 deg`, `art_w`, `art_h`, `art_margin`, `art_pocket_d`, `art_cy`, `pocket_w`, `pocket_h`, `vent_z0`, `vent_z1`, `vent_groove_d`, `vent_n`, `vent_w`, `vent_h`, `web_w = 8 mm`, `web_z1 = 40 mm`, `insert_hole_d`, `insert_hole_h`; body **cup**; plane `lid_top` (z = `drum_h`); features `cup_wall`, `cup_lid`, `btn_holes`, `art_pocket`, `col_<n>`, `web_<n>`, `col_insert`, `vent_groove`, `vent_slot`, `vent_slot_pattern`, `joint_chamfer_cup`, `joint_chamfer_base`.

**Confidence:** 90%. Revolve, chamfer-by-predicate and the web join are new combinations of known calls; the spike-proven mapping rule covers the tangent-plane sketches.

- [ ] **Step 1: Write `cad/pi_drum_c.py`**

1. Wall: sketch on `split`, ring ⌀`drum_d` / 2·`cavity_r`, extrude `drum_h - lid_t - split_z` new body → `cup`. Lid: sketch on `lid_top`, circle ⌀`drum_d`, extrude `-lid_t` join. Oracles: ring and disc volumes.
2. Button holes: one sketch on `lid_top`, six circles ⌀`btn_hole` at `btn_ring_r * cos(btn_ang_x)` / `sin`, jittered seeds, one `through_cut` through the lid only (`blind_cut` of `lid_t + 1 mm` downward). Oracle: 6·π·(d/2)²·`lid_t`; **containment at each signed centre** at z `drum_h - lid_t/2` is empty and at the centre + 16 mm in x is solid.
3. Art pocket: `bound_rect2` `pocket_w` × `pocket_h` at (0, `art_cy`) on `lid_top`, `blind_cut` `art_pocket_d`. Oracle: w·h·d. Read-back: one planar face at z `drum_h - art_pocket_d` of area w·h; corners solid at z 114.6 and empty at z 114.2.
4. Webs first, then columns. A join whose tool does not touch the target adds nothing and reports success (skill, measured), and the column cylinder at r 72.8 ± 4 stops 0.2 short of the cup wall. So: on a plane at z `web_z1`, four rectangles `web_w` wide (tangential) from r `col_r` to r `cavity_r + 1 mm` on each column's radial line (a radial plane per column as in stage O, or `bound_rect2` with cos/sin position expressions), extrude downward `web_z1 - split_z` **join** → the webs overlap the wall by 1 mm. Oracle: 4·web volume minus the wall overlap. Then four circles ⌀`col_d` at (`col_r * cos(±20 deg)`, `col_r * sin(±20 deg)`) etc. on the same plane, extrude downward `web_z1 - col_foot_z` **join** → each column overlaps its web over z 32–40. Oracle: 4·π·(d/2)²·h minus the column–web overlap (computed). Assert `root.bRepBodies` has exactly two bodies named `base` and `cup` and that `cup.volume` includes the columns. Containment: solid at r 77.2 on each column's radial line at z 36 (in the web), solid at the column axis at z 10, empty at r 80.5.
5. Column inserts: four circles ⌀`insert_hole_d` on a plane at z `col_foot_z`, blind cut upward `insert_hole_h`. Oracle: 4·π·(d/2)²·h.
6. Exhaust groove: sketch on XZ, rectangle `vent_groove_d` × (`vent_z1 - vent_z0`) at x from `drum_r - vent_groove_d` to `drum_r`, revolve 360° about the Z axis as a cut. Oracle: π·(r_o² − (r_o − d)²)·(z1 − z0).
7. Vent slots: one radial plane at 0°, rectangle `vent_w` × `vent_h` centred at z `(vent_z0 + vent_z1)/2`, blind cut inward `wall_t + 1 mm`; circular pattern quantity `vent_n`, `AdjustPatternCompute`. Oracle: face-count delta ≥ 3·(n − 1); containment empty at r 78.5 on the last instance's angle.
8. Joint chamfers: `chamferFeatures` with `joint_chamfer` on the circular edge of `cup` at z `split_z`, r `drum_r` (predicate: circle edge, radius, z) and on the circular edge of `base` at the same place. Oracle: each chamfer removes (c²/2)·2π·(r − c/3) within 1 %.
9. Measure the gap: `measureManager.measureMinimumDistance(col_<n> face, base inner wall)` is awkward with faces; instead containment: on each column's radial line at z 20, solid at r 76.7 (column) and empty at r 76.9 (gap) and solid at r 77.1 (base wall). Interference check cup/base: the verify block runs it; expected none.

- [ ] **Step 2: Bundle, gate, execute.** Expected: pass; two bodies; the cup volume about 95 cm³ (reported, then asserted against the analytic sum).

- [ ] **Step 3: Renders** `cad/renders/pi_drum_stageC_iso.png`, `_top.png`, `_section.png` (section analysis is manual; a view from below with the base hidden stands in: `base.isVisible = False`, save, restore).

- [ ] **Step 4: Commit** `"Stage C: the cup, buttons, art pocket, columns and vents (D-021)"`.

---

### Task 6: Stage D, the livery

**Files:**
- Create: `cad/pi_drum_d_probe.py` (throwaway, kept for the record), `cad/pi_drum_d.py` (+ bundled)
- Create (outputs): `cad/art/drum/sf2_front.dxf`, `sf2_front_holes.dxf`, `chunli_left.dxf`, `ryu_right.dxf` (Ryu only once OI-012 supplies a source; otherwise `chunli_right.dxf`, a mirrored copy, and the spec's open item stands)

**Interfaces:**
- Consumes: `cup`; art-space DXFs from Task 2; `drum_art.py place`.
- Produces: parameters `inlay_d`, `logo_z`, `sil_z`, `logo_w`, `logo_h`, `sil_w`, `sil_h`; planes `art_front` (XZ offset `-drum_r`), `art_left` (YZ offset `-drum_r`), `art_right` (YZ offset `+drum_r`); sketches `sf2_solid`, `sf2_holes`, `sil_left`, `sil_right`; features `logo_deboss`, `logo_counters`, `logo_inlay_copy`, `logo_inlay`, `sil_left_deboss`, `sil_left_inlay`, `sil_right_deboss`, `sil_right_inlay`; bodies `inlay_logo`, `inlay_left`, `inlay_right`.

**Confidence:** 93%. Both mechanisms were proven in scratch-document spikes on 2026-10-22: `embossFeatures.createInput([profiles], [face], "-1.2 mm")` wraps and removes area × depth × ((r − d/2)/r) exactly; `+1.2 mm` on the recess floor fills a counter back flush, adding area × depth × ((r_floor + d/2)/r_floor); `copyPasteBodies` before, `combineFeatures` cut with `isKeepToolBodies = True` after, yields the inlay to 1e-12 cm³. The `operation` setter needs `# pyright: ignore[reportAttributeAccessIssue]` (known stub gap). What remains unproven is the 1,076-curve logo sketch as emboss input, which the one-letter first step covers.

- [ ] **Step 1: Mapping probe**

`cad/pi_drum_d_probe.py`: create the three planes, a sketch on each, print `sketchToModelSpace` of (0,0), (1,0), (0,1) per plane as `FH_RESULT {...}`, and delete the sketches and planes. Run it. Record the three mappings in the script's docstring. (Measured today for the front plane: origin (0, −80, 0), sketch x → +x, sketch y → −z, so the front needs `--flip-y`.)

- [ ] **Step 2: Place the DXFs**

For each art piece run `drum_art.py place` with `--cx 0 --cy ±logo_z` (sign per the probe's y mapping) and `--flip-y` where sketch y maps to −z. Expected last lines: bboxes centred at (0, ±67) with the art sizes.

- [ ] **Step 3: Write `cad/pi_drum_d.py`**

1. Parameters; planes.
2. `check_placement` as stage M: after `sketch.importDXF`-equivalent (`importManager.createDXF2DImportOptions`, target sketch's plane), assert the imported curves' model-space bbox: x centre 0 ± 0.05, z centre `logo_z` ± 0.05, size `logo_w` × `logo_h` ± 0.05. A mismatch raises before any cut.
3. First execute with only the first letter? The DXF is one file; instead the first execute debosses the whole `sf2_solid` sketch with the counters step skipped and `FH_ATTEMPT = 1`, asserting the volume delta = Σ profile areas × `inlay_d` × ((r − d/2)/r) within 0.5 %. If it fails, undo (`fusion_run` has no undo; use Fusion's Edit → Undo, the script rolled back atomically anyway) and bisect by exporting a one-letter DXF with `place` on a hand-cut copy.
4. Face selection (Review Focus 4): among `cup.faces`, cylindrical, radius `drum_r`, bbox z min ≤ 35 and z max ≥ 99; assert exactly one.
5. `logo_inlay_copy` = `copyPasteBodies.add([cup])` **before** `logo_deboss`; then `logo_deboss` (−`inlay_d`); then `logo_counters` (+`inlay_d` on the recess-floor face: cylindrical, radius `drum_r - inlay_d`, exactly one); then `logo_inlay` = combine cut (target the copy, tool `cup`, keep tools), rename the copy `inlay_logo`. Oracle: `inlay_logo.volume` = cup volume before − cup volume after, 1e-6.
6. Repeat for `sil_left` on `art_left` and `sil_right` on `art_right` (no counters).
7. Read-back: containment on the front radial line at z `logo_z`: empty at r 79.5 inside a letter stroke (the DXF's first polyline centroid), solid at r 78.5; the inlay solid at r 79.5 at the same point. Bodies: exactly five, named `base`, `cup`, `inlay_logo`, `inlay_left`, `inlay_right`; `FH_OPTS["max_bodies"] = 5`; `force_liveness = True` and the imported sketches' `sketch.unconstrained` finding documented as the stage M exception.

- [ ] **Step 4: Bundle, gate, execute.** Expected: pass apart from the documented constraints finding on the four imported sketches.

- [ ] **Step 5: Renders** `cad/renders/pi_drum_stageD_front.png`, `_left.png`, `_right.png` with the inlay bodies shown in red (`appearance` is cosmetic; skip if it costs an execute).

- [ ] **Step 6: Commit** `"Stage D: wrapped SF2 logo and silhouettes with inlay bodies (D-021)"`.

---

### Task 7: Stage E, export, renders and the record

**Files:**
- Create: `cad/pi_drum_e.py` (+ bundled), `cad/exports/pi_drum.step`, `cad/exports/pi_drum.3mf`, `cad/renders/pi_drum_stageE_*.png`
- Modify: `docs/docs/09-decision-log.md` (a *Consequences* addendum under D-021 with the five volumes), `docs/CLAUDE.md` (current phase line), `.claude/skills/fusion-design/VENDORED.md` if anything about the toolchain changed.

**Interfaces:**
- Consumes: the five bodies.
- Produces: `exportManager.createSTEPExportOptions(filename)` for the whole design and `createC3MFExportOptions(root, filename)` (both present in the stubs); the renders; the docs lines.

**Confidence:** 92%. Export calls are in the stubs; the 3MF option's exact body-selection behaviour is unverified, so STEP is the primary deliverable and the 3MF is a bonus.

- [ ] **Step 1: Write `cad/pi_drum_e.py`**: an overhang audit per body in its print orientation (cup is printed inverted: audit with normals flipped), using the face-normal sweep from the skill (`normal.z < −0.7075` flagged, floor faces skipped); the five-body check; exports; six renders (iso, front, left, top, base from above with the cup hidden, cup from below with the base hidden). No geometry changes, so the verify block runs with `liveness: False`.

- [ ] **Step 2: Bundle, gate, execute.** Expected: pass; overhang audit lists zero faces for the base and zero for the cup in print orientation; STEP about 1–3 MB written.

- [ ] **Step 3: Slice check (owner's machine, Bambu Studio)**: import the STEP, confirm five parts, assign red to the three inlays, confirm the cup's first-layer colour changes are three layers. Record the result in D-021's addendum.

- [ ] **Step 4: Docs**: D-021 addendum (volumes, export path, the slice check), CLAUDE.md current phase ("console drum modelled, awaiting sockets (OI-013) and the first print").

- [ ] **Step 5: Commit** `"Stage E: exports, overhang audit, renders; D-021 addendum"`.

---

## Owner actions outside the plan

- Create and save the Fusion document **Pi Console Drum** before Task 3.
- Buy the four panel-mount sockets and the heatsink kit; measure the flanges (OI-013) and set Task 4's placeholders before printing the base.
- Measure the M2.5 inserts' recommended bore and set `pi_insert_hole`.
- Supply a Ryu image (OI-012) or accept the mirrored Chun-Li.
- Optionally register the MCP server for this project (`claude mcp add --transport http fusion http://127.0.0.1:27182/mcp`); the launcher does not need it.
- After the first print: the thermal and fit checks in `07-testing.md`.
