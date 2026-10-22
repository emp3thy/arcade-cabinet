# Pi console drum — design

*Date:* 2026-10-21 · *Status:* approved by the owner 2026-10-22 ·
*Supersedes:* the "Pi console box" section of
`docs/docs/06-enclosure-reference.md` (a box with six buttons on top).
Recorded as **D-021** in the decision log.

Layout study with drawings: https://claude.ai/artifact/YHhTVcemvKwXMGXPjn4Gu1

## 1. Intent

The stationary unit next to the projector: a Raspberry Pi 4B running RetroPie
and the six system buttons (Player 1–4 Start, Select, Hotkey) wired to GPIO
(`04-wiring-pi-console.md`). The owner wants it to be fun rather than a box:
a cylinder in Street Fighter II livery that matches the lap pads, so the pads
and the console read as one set on the shelf.

Success: the Pi runs an evening of SF2 without throttling; the buttons sit in
player order and are obviously not gameplay buttons; the console comes apart
for service without tools touching the outside; every part prints without
support on the owner's Bambu printers; the livery uses the art already
prepared for the pads.

What the owner said (2026-10-21): cylinder, SF2 livery on the side; two
colours on the H2D's dual nozzles for the side, full multi-colour art on the
top; drum not barrel; panel-mount sockets; heatsink and vents, no fan; model
six buttons now and accept a reprint if OI-005 fails; M2.5 inserts for the Pi;
black drum with a red logo on the front and red character silhouettes on the
sides; base and floor in PETG, the shell with the buttons in PLA, the two
bolted together; bolts from below.

## 2. Form

A ⌀160 × 115 drum in two bolted parts.

| Part | Material | Extent | Carries |
|---|---|---|---|
| **Base** | PETG black | z 0–32: floor and the lower wall, one piece | Pi on four insert bosses, four socket pads with the panel-mount sockets, intake vents, four countersunk fixing holes |
| **Cup** | PLA black, red inlays | z 32–115: the upper wall and the lid, one piece | six buttons, the multi-colour art pocket, the side livery, the exhaust vents, four columns that take the fixing screws |

Model frame: origin on the drum axis at the underside of the base, x to the
player's right, **y toward the back** (away from the player), z up. Angles
are measured from +x toward +y, so the front is −90° and the back +90°.

The parting line at z 32 sits above the socket flanges (z 6–30) and below
the Pi's Dupont leads (to about z 35), which pass up into the cup. Lifting the
cup lifts the buttons and their leads; the leads unplug at the header.

## 3. Parameters

All `snake_case`, one value stated once, derived values as expressions
(fusion-design R1, R7). Placeholders that wait on a measurement are marked.

| Parameter | Value | Note |
|---|---|---|
| `drum_d` | 160 | outside diameter |
| `wall_t` | 3 | both parts |
| `drum_h` | 115 | overall, floor underside to lid top |
| `split_z` | 32 | parting line |
| `floor_t` | 3 | base floor |
| `lid_t` | 5 | cup lid |
| `fit_clear` | 0.25 | radial clearance where printed parts nest (as the pad's plate) |
| `col_clear` | 0.2 | column to base wall |
| `btn_hole` | 30.5 | 30 mm screw-in button, as the pad |
| `btn_ring_r` | 57 | button centre radius |
| `btn_arc_pitch` | 41 deg | Start-to-Start angle; chord 2·57·sin(20.5°) = 39.9 |
| Start angles | −151.5, −110.5, −69.5, −28.5 deg | P1 to P4, left to right across the front |
| Pair angles | 160, 20 deg | SEL, HK |
| `art_w`, `art_h` | 45.7, 64 | the pad's Chun-Li, `cad/lap_disc_g.py` |
| `art_margin` | 2.2 | pocket margin, as the pad |
| `art_pocket_d` | 0.6 | three 0.2 layers |
| `art_cy` | 20 | pocket centre on the y axis, behind the middle |
| `col_r` | 72.8 | column centre radius; column spans r 68.8–76.8 against the cup's inner wall at 77 |
| `col_d` | 8 | column diameter |
| `col_foot_z` | 6 | column foot, on the base floor's top face |
| Column angles | −20, −160, 160, 20 deg | (±68.4, ∓24.9) |
| `pad_w` | 30 | socket pad flat width; sagitta on r 80 is 1.42 |
| `pad_back_t` | 5 | wall thickness behind a pad, so flange screws have thread |
| Pad angles | 45, 75, 105, 135 deg | RJ45, USB-C, HDMI, USB-A pair, right to left seen from behind |
| `pad_z0`, `pad_z1` | 6, 30 | pad height band |
| `*_cut_w`, `*_cut_h`, `*_screw_pitch` | **placeholders** | one set per socket; measured on arrival |
| `pi_hole_px`, `pi_hole_py` | 58, 49 | Pi 4B hole pitch |
| `pi_boss_d`, `pi_boss_h` | 6, 5 | insert bosses |
| `pi_insert_hole` | 3.4 | **placeholder** for the owner's M2.5 inserts |
| `intake_n`, `intake_d`, `intake_r` | 24, 5, 62 | floor holes, outside the Pi's footprint (bosses at r 38) |
| `notch_n`, `notch_w`, `notch_h` | 8, 12, 3 | rim notches so air reaches the floor holes |
| `vent_z0`, `vent_z1`, `vent_groove_d` | 101, 105, 1.2 | exhaust shadow groove |
| `vent_n`, `vent_w`, `vent_h` | 16, 8, 2.5 | slots through the groove floor |
| `joint_chamfer` | 0.8 | 45° on both outer edges at z 32 so the joint reads as a line |
| `insert_hole_d`, `insert_hole_h` | 4, 4.2 | M3 heat-set, as the pad (D-016) |
| `screw_clear_d` | 3.4 | M3 clearance |
| `csk_d` | 6.5 | 90° countersink for M3 flat heads |
| `logo_w`, `logo_h` | 116.98, 59.78 | `cad/art/logo/sf2_deboss_solid.dxf`, as D-018 |
| `logo_z` | 67 | logo centre height; band z 35–99 |
| `inlay_d` | 1.2 | deboss depth; 1.8 of wall left |
| `sil_w`, `sil_h` | 42, 59 | silhouettes, the art's 0.714 aspect |
| `sil_z` | 67 | |

## 4. Base

- **Floor:** ⌀160 × 3, z 0–3. Twenty-four ⌀5 intake holes on r 62 at 15°
  steps. Eight 12 × 3 notches in the outer rim at 45° steps starting at
  22.5°, so the drum stands on eight feet and air reaches the floor holes.
- **Wall:** r 77–80, z 3–32. The top outer edge carries the joint chamfer.
- **Socket pads:** four, on the back half at 45°, 75°, 105°, 135°, each a
  vertical flat 30 wide spanning z 6–30, cut 1.42 into the outside of the
  wall (the chord at r 78.58), with the wall thickened inward to 5 behind
  the pad so the flange screws bite. Each pad gets its socket's cutout and
  two screw pilots from the placeholder parameters.
- **Pi bosses:** four ⌀6 × 5 at (±29, ±24.5), z 3–8, insert holes
  `pi_insert_hole` × 4 deep. The Pi sits centred, HDMI edge toward +y, USB
  edge toward +x. Lead room from the probe: 42–49 mm behind the HDMI edge,
  32–35 mm beside the USB edge. microSD on the −x side, reached by lifting
  the cup.
- **Fixing holes:** four ⌀3.4 at r 72.8 on the column angles, countersunk
  from below ⌀6.5 × 90°.
- **Heatsink:** the Pi 4 heatsink kit on SoC, RAM and USB controller; no
  model feature.

Prints open side up, no overhang except the pad thickening, which is
vertical.

## 5. Cup

- **Wall:** r 77–80, z 32–110; **lid:** ⌀160 × 5, z 110–115, one body.
  Bottom outer edge carries the joint chamfer.
- **Buttons:** six ⌀30.5 through the lid at r 57: P1 (−50.1, −27.2),
  P2 (−20.0, −53.4), P3 (20.0, −53.4), P4 (50.1, −27.2), SEL (−53.6, 19.5),
  HK (53.6, 19.5). Nearest pair P1–SEL at 46.8 centres (16.3 of material);
  Start pairs at 39.9 (9.4). Hole edges reach r 72.2, 4.8 inside the wall.
- **Art pocket:** 50.1 × 68.4 × 0.6 into the lid's top face, centred
  (0, 20). Probe: 13.0 clear of P1/P4, 13.3 of SEL/HK, 24.1 of P2/P3, its
  corners at r 59.7. The art SVG layers import exactly as on the pad
  (stage G and the Bambu layer sets in `cad/art/layers/`).
- **Columns:** four ⌀8 from z 40 down to z 6, tangent to the cup's inner
  wall, with a 2 × 8 web between column and wall over z 32–40 so the joint
  is more than a line contact. Inside the base the column clears the base
  wall by `col_clear`. M3 insert hole ⌀4 × 4.2 in each foot.
- **Exhaust:** a 4 tall × 1.2 deep groove round the outside at z 101–105,
  sixteen 8 × 2.5 slots through its floor at 22.5° steps.
- **Livery:** three debosses of `inlay_d` wrapped onto the outer cylinder
  with Fusion's emboss feature (`embossFeatures.createInput(profiles,
  faces, depth)`, negative depth): the logo at the front (−90°) centred at
  z 67, Chun-Li at 180° (the player's left), Ryu at 0°. For each, a copy of
  the cup body taken before the deboss, minus the cup after it, is the red
  inlay body; it is kept as a separate body in the same component so the
  slicer assigns it to the second nozzle. Five bodies export: cup, three
  inlays, base.

Prints open side up: the lid's top face is on the bed, so the art pocket
and the button holes are the first layers and the colour swaps happen in the
first three layers. The columns point up during printing and need no
support. The exhaust groove faces outward; its slots are horizontal through
a 3 mm wall and bridge.

## 6. Hardware and purchases

Additions to `02-bom.md`, Pi console box section:

| Item | Qty | Status |
|---|---|---|
| Panel-mount HDMI extension, micro-HDMI male to HDMI female, ≤ 30 cm | 1 | NEEDED |
| Panel-mount USB-C extension (power) | 1 | NEEDED, already listed |
| Panel-mount USB-A ×2 extension | 1 | NEEDED |
| Panel-mount RJ45 coupler | 1 | NEEDED |
| Pi 4 heatsink kit | 1 | NEEDED |
| M2.5 heat-set inserts, M2.5 × 6 screws | 4 + 4 | NEEDED |
| M3 heat-set inserts (the pad's) | 4 | HAVE |
| M3 × 10 countersunk | 4 | NEEDED |
| Black PETG, black PLA, red PLA | — | owner's stock |

## 7. Build plan (CAD)

A new Fusion document `pi_drum`, author scripts under `cad/pi_drum_*.py`,
bundled and gated as the pad scripts are (`VENDORED.md`). Each stage ends
with the fusionhelper verification block and its own analytic oracles.

- **Stage A — base.** Parameters, floor, wall, intake holes and notches, Pi
  bosses, fixing countersinks. Oracles: volume per feature; point
  containment on every hole; boss positions.
- **Stage B — socket pads.** Four pads with placeholder cutouts and pilots.
  Oracle: pad floor is planar at r 78.58; wall behind each pad ≥ 5.
- **Stage C — cup.** Wall, lid, button holes, art pocket, columns, joint
  chamfers, exhaust groove and slots. Oracles: hole centres; pocket volume;
  column foot height; no interference with the base and `col_clear`
  measured; overhang audit in print orientation.
- **Stage D — livery.** Logo deboss and inlay. Starts with a spike: one
  letter wrapped, measured, before the whole DXF. Then the two silhouettes,
  which need their DXFs (below). Oracle: inlay volume ≈ profile area ×
  `inlay_d` × (r 79.4 / 80); cup volume drops by the same amount.
- **Stage E — assembly and renders.** Cup on base, interference check,
  clearances, renders for the owner, STEP/3MF export of the six bodies.

Art preparation, outside Fusion: a script in `cad/art/` that unions the
Chun-Li layer SVGs into one silhouette and writes a DXF scaled to
`sil_w` × `sil_h`; the same script handles Ryu once a source image exists.

## 8. Verification and testing

- Every script passes `fusionhelper.preflight` on the bundled artefact and
  prints a green `FH_VERDICT1` with liveness scoped to its parameters.
- Overhang audit by face-normal sweep in print orientation for both parts.
- Interference check cup against base: none; measured gap at the columns
  equals `col_clear` ± 0.01.
- First print: fit the buttons, the Pi, four sockets and the cup; record
  what misfits as a D-02x entry, as D-020 did for the pad.
- Add to `07-testing.md` section D: twenty minutes of SF2 with
  `vcgencmd measure_temp` logged every ten seconds, bare board on the bench,
  then assembled in the drum with the heatsinks; pass if the assembled SoC
  stays under 70 °C and the air under the lid under 50 °C (a thermocouple
  or the owner's hand on the lid is enough for the second).
- OI-005 stays open; its outcome decides whether the cup is reprinted with
  only the rear pair.

## 9. Documentation after approval

- `09-decision-log.md`: D-021, pointing here.
- `06-enclosure-reference.md`: replace the Pi console box section with the
  drum numbers.
- `02-bom.md`: section 6 above.
- `07-testing.md`: the thermal check.
- `08-open-issues.md`: OI-012 Ryu art source; OI-013 socket dimensions.
- `CLAUDE.md` file map and current phase.

## 10. Open items

- Ryu source image. Until it exists the right side gets nothing, or Chun-Li
  mirrored.
- Socket flange dimensions, on arrival.
- The owner's M2.5 insert size.
- The Fusion MCP server must be registered for this project before any
  stage runs: `claude mcp add --transport http fusion
  http://127.0.0.1:27182/mcp`, then a new session.

## 11. Assumptions

Status: **verified** (checked on this machine today), **measured** (an
earlier owner measurement in the docs), **unverified** (planned check
named).

| # | Assumption | Status | Cost if wrong |
|---|---|---|---|
| A1 | Pi 4B port centres: USB-C 11.2, HDMI 26 and 39.5, AV 54 along the long edge; USB2 9, USB3 27, ethernet 45.75 along the short edge | unverified: from memory of the official drawing; the repo's STEP is a 3-block placeholder with no port geometry (probe today) | low: the extension leads absorb a few mm; only lead room changes. Check: measure the board or import Pi's own STEP |
| A2 | Pi with Dupont leads reaches z 35 | unverified; check with the crimped leads in hand | low: 25 mm margin to the button bodies |
| A3 | Button hole 30.5, fitted depth 50 | measured (D-013; the pad's first print took the buttons) | — |
| A4 | Art 45.7 × 64; logo 116.98 × 59.78 | verified from `cad/lap_disc_g.py` and `cad/lap_disc_m.py` | — |
| A5 | Fusion's emboss is in the API and wraps a 1.2 deboss onto the cylinder | API presence verified in the Fusion Python stubs today (`EmbossFeatures.createInput(profiles, faces, depth)`); wrapping behaviour unverified until stage D's spike | medium: fallback is a flat facet behind each art piece, which changes the look |
| A6 | Inlay body = cup before deboss minus cup after | unverified; stage D | low: alternative is a positive emboss on a copy intersected with the recess |
| A7 | 1.2 mm red PLA inlays print cleanly in dual-nozzle mode on the H2D | unverified; a 40 mm coupon before the cup | low: depth or colour order change |
| A8 | A PLA cup with six button bodies survives the drum's internal temperature | unverified; the thermal bench check | medium: cup reprinted in PETG with a PETG colour set |
| A9 | Heatsinks plus chimney vents keep the SoC under 70 °C in SF2 | unverified; the thermal bench check | low: a 30 mm fan on the floor is a later stage |
| A10 | Each panel-mount socket fits a 30 mm flat between z 6 and 30 | unverified; measured on arrival | medium: pad width, or the parting line, moves |
| A11 | M2.5 inserts take a ⌀3.4 hole | unverified; the owner's inserts | low: one parameter |
| A12 | M3 inserts take ⌀4 × 4.2 | measured (D-016, printed on the pad) | — |
| A13 | 0.2 radial clearance seats the columns | unverified; first print | low: one parameter, reprint the cup |
| A14 | The Chun-Li layer SVGs union to one usable silhouette | unverified; the art script is a spike before stage D | low: trace the silhouette by hand |
| A15 | The toolchain runs: bundler and preflight under uv with FusionHelper editable | verified today on `cad/lap_disc_o.py`: bundle ran, preflight exit 0. The gate also reported *stub fingerprint drifted: Fusion update changed the API defs; re-run gate fidelity tests and re-bless the lock*, a FusionHelper maintenance item, not a script fault | low: re-bless the lock in FusionHelper before stage A |
| A16 | Layout clearances: Start chord 39.9, P1–SEL 46.8, pocket 13.0 from the nearest hole, columns 11° clear of the nearest pad, Pi corners 26 from the columns | verified by probe today | — |
| A17 | 115 tall and ⌀160 fit every printer: X1 Carbon 256 × 256 × 256, H2D dual-nozzle 300 × 320 × 325 | verified against `06-enclosure-reference.md` | — |
| A18 | OI-005 passes, so six buttons are right | unverified; the owner accepted the reprint risk | low: reprint the cup with two holes |
| A19 | Lead room: 42–49 mm behind the HDMI edge, 32–35 beside the USB edge, enough for extension plugs | verified by probe for the geometry; plug lengths unverified until the parts arrive | low: shift the Pi toward the front, 20 mm available |
