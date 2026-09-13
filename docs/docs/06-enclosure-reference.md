# 06 — Enclosure Reference Data

Enclosure CAD is done by Claude in Fusion 360 through the `fusion-design` skill
at `../../.claude/skills/fusion-design/` (**D-011**, 2026-09-06, superseding
D-008). The owner reviews, prints and owns the result. This file holds the
dimensions, clearances and placement the model is built from — it is the input
to that model, not a substitute for it.

`../Lap_Pad_Enclosure.scad` is stale reference only: it predates D-010 and D-011
and is defective as geometry (see the note at the end of this file). STEP models
of the components live in `../STEP_Reference_Files/`.

## Component footprints — lap pad

| Component | Dimensions (mm) | Mounting |
|---|---|---|
| Brook Gen 5W | 97 × 52 (a verified 96 × 45 STEP also exists — **measure yours**) | 4× corner M3 |
| LiPo 103395 | 95 × 33 × 10 | strapped/foamed, no hard mount |
| ~~TP4056 module~~ | ~~26 × 17~~ | **Removed by D-010** — do not allocate space or standoffs |
| ~~Qi receiver coil~~ | ~~⌀50, 1.5 mm thick~~ | **Removed by D-015** — no coil boss, no ring hole |
| USB-C port board | ~30 × 26 board, holes ASSUMED 24 × 20 — **measure; also state whether the socket is upright or edge-mounted, which decides the mount** | In the rear facet window (30.4 × 26.4), wired to the Brook's USB-C input; pigtail needs slack and strain relief (D-015) |
| OLED module | 27 × 15 active area | panel cutout |
| Joystick (from the cabinet — cross-pattern plate, so probably not a Sanwa JLF despite the STEP file) | **21 mm shaft hole** (measured on the steel plate, 2026-09-12; cut the printed plate at 22 mm so the steel edge is the limit); **4 mounting holes on the axes, each 16 mm from the shaft centre** (owner, 2026-09-12) | **4× M3 × 12 mm bolts through the top plate into the stick's mounting plate, nuts below (owner, 2026-09-12)**. Heads countersunk into the 3.5 mm plate. A **steel plate, 53 mm wide (left–right) × 95 mm front-to-back × 1 mm thick** from the cabinet goes between the stick and the printed plate as a stiffener; give the underside of the top plate a matching 1 mm pocket, centred on the stick (x 48.5–101.5, y 52.5–147.5 in the study's coordinates). It already has the shaft hole and the four M3 holes in the right places, so it doubles as the template for the printed plate's holes (owner, 2026-09-12). |
| Action buttons | ⌀30 hole, snap-in; **40 mm below-panel depth** (measured 2026-09-12: from the top surface of the hole to the bottom of the microswitch) | — |

> Two different Brook footprints appear in the STEP folder
> (`Brook_Gen5W_96x45_VERIFIED.step` and `Brook_Gen5W_97x52.step`). Take
> callipers to the actual board before cutting standoffs. The `_VERIFIED` file
> is the better bet but the SCAD reference uses 97 × 52.

## Draft lap pad envelope

The SCAD reference uses **300 × 200 × 40 mm** with 10 mm corner radius, 3 mm top
plate, 2 mm walls, 35 mm internal depth.

**Printer fit, confirmed 2026-09-06 against manufacturer specs:**

| Printer | Single nozzle (W × D × H) | Dual nozzle |
|---|---|---|
| H2C | 305 × 320 × 325 mm | 300 × 320 × 325 mm |
| H2D | 325 × 320 × 325 mm | 300 × 320 × 325 mm |

**Print lap pads on the H2D in single-nozzle mode** (settled 2026-09-06; closes
`08-open-issues.md` OI-006)**.** That leaves 25 mm of
headroom on X. The H2C works single-nozzle only, with 5 mm total — 2.5 mm a side,
which is inside the noise of a brim or any warp on a 300 mm part. In dual-nozzle
mode the H2C is exactly 300 mm, so it will not slice with a brim at all. The
X1 Carbon's 256 mm bed is out for a one-piece pad.

No need to split the part or shrink it for the bed. Depth is a non-issue
everywhere: 200 mm against a 320 mm Y.

Other reference parameters from the SCAD file:

- Joystick centre: x 80, y 100 from the front-left corner. **Current design
  (enclosure study): stick centre to nearest button centre 63 mm, confirmed by
  the owner against an old joystick template on 2026-09-12. Button pitch 40 mm
  centre to centre, both directions, and 8 mm second-row offset, both confirmed
  against the same template.**
- Button cluster: first button at x 170, y 70; 36 mm horizontal pitch,
  30 mm row pitch, 12 mm offset on the second row (3 × 2 layout)
- OLED cutout at x 150, y 170
- ~~USB-C access slot 12 × 8 mm on the front edge at x 145~~ — **deleted by
  D-010.** No external USB-C port. Firmware updates mean opening the pad.
- ~~TP4056 standoffs at x 220, y 80~~ — **deleted by D-010.**
- Snap-fit tabs 15 × 5 × 2 mm at 60 mm spacing, 0.3 mm tolerance
- Standoffs 8 mm tall, 6 mm OD for M3
- Anti-slip foot recesses ⌀10 × 1.5 mm deep, 15 mm inset

> **The SCAD file has not been updated for D-010 or D-011** and still models both the
> USB-C slot and the TP4056 standoffs. It also has geometry defects independent
> of this decision — mixed centre-origin and corner-origin coordinates, a 90 mm
> Brook hole pitch that cannot fit a 52 mm board dimension, a ventilation slot
> that falls outside the body, and foot recesses that subtract from nothing.
> Treat its numbers as reference, not as a starting model.

## Clearances to design in

- **Battery**: pouch cells swell over their life. Leave ~2 mm of clearance on
  the large faces and do not clamp it. Keep it away from the Brook's charging
  circuit for thermal reasons.
- **Joystick**: bolts directly to the underside of the top plate through the
  1 mm steel stiffener (4× M3 × 12, confirmed 2026-09-12), so there is no plate
  drop. **Body is 34 mm deep below the steel plate (owner, 2026-09-12)**, so its
  bottom sits 37.5 mm below the panel face with the steel in its 1 mm pocket.
  Add ~4 mm for the harness plug and 2 mm floor: 43.5 mm needed against 54 mm
  of shell at the stick on the 48/60 profile. 10.5 mm spare. **Body footprint
  below the plate is 75 × 65 mm (owner, 2026-09-12)**; assumed 75 mm
  front-to-back to match the plate's long axis — confirm. Centred on the stick
  that is x 42.5–107.5, y 62.5–137.5, which clears the Brook (y from 144) by
  6.5 mm.
- **Buttons**: 30 mm snap-ins want a panel thickness of roughly 2.5–5 mm to
  latch properly. The 3 mm top plate is in range.
- **Button depth (measured 2026-09-12): 40 mm from the top surface of the panel
  to the bottom of the button.** With a 3 mm top plate that is 37 mm of
  intrusion into the cavity. **The SCAD envelope's 35 mm internal depth does not
  fit this** — the button bottom would sit level with the outer face of the
  floor. Budget 40 mm button + ≥5 mm for microswitch spade terminals and wire
  bend + 2 mm floor, i.e. **≥47 mm overall height under the button cluster**,
  or a local pocket in the floor. This is the same number for the Pi console
  box top face. **The current design is not the SCAD envelope but the 26/46
  saddle wedge in the Lap Arcade Enclosure Study
  (https://claude.ai/code/artifact/28289a89-8921-427e-a3c4-b8082337952b),
  which is slimmer still — 28.5 mm internal at the kick row before the scoop.
  The study's own gate said over 35 mm reopens the profile; 40 mm does.
  Re-settled the same day (D-013): the buttons and their straight
  quick-disconnects stay, and the pad grows to a **48 mm front / 60 mm rear**
  wedge with a flat underside and 3 mm TPU contact ridges; the R900 scoop is
  deleted. Fitted button depth with connector and unstressed wire is ~50 mm;
  shell under the button cluster is 52.8–55.2 mm against a 52 mm minimum.
  Flag connectors (42/54) and shallower Seimitsu/Sanwa buttons (38/50, the
  stick's floor) were considered and rejected as not worth it.**
- **Lap ergonomics**: 200 mm depth on a lap is a lot. Consider a slight wedge
  (5–8°) and rounded front edge. Underside feet only matter for table use.

## Pi console box

| Component | Dimensions (mm) | Notes |
|---|---|---|
| Raspberry Pi 4B | 85 × 56 | 4× M2.5, 58 × 49 hole pitch, 3.5 mm edge inset |

Openings needed: HDMI (micro-HDMI ×2), USB-C power, ethernet, USB-A ×2,
microSD access, and ventilation. Six 30 mm buttons on the top face. A panel-mount
USB-C extension keeps the power inlet tidy.

The Pi 4 throttles in a sealed box. Passive vents plus a heatsink is the minimum;
a 30 mm fan is safer if it's running for hours.

## Comfort study (2026-09-12)

Four research reports and three design variants live in `../comfort-study/`
and are summarised in section 14 of the enclosure study artefact. Common
ground across all three variants: keep 48/60; round the front edge (R8–R12);
soft palm rest at least 38 mm deep in the front band (displaces the art
inlay); move the button rows 11–16 mm toward the knees and drop the index
column 10–14 mm so the stick sits level with the near row; widen the thigh
contact well beyond two narrow strips. Round two replaced the two non-conservative variants with real forms: a
Star Trek TNG conn-station fan (296 × 250, flat panel at 54, undercut front
lip, rear brow to 70) and a ⌀300 nested-disc pad (52 thick, rotatable, full
TPU ring underneath); a base-forward triangle was worked through and rejected.
Plan views are the `plan-*.svg` files. Open: which form to build (box, fan or
disc; recommendation: three foam mock-ups first), the thigh slope on the
beanbag, and the template's second-row offset direction. **Decided (D-014, 2026-09-12): the disc.**

## Lap pad — current form (D-014)

⌀300 nested disc, 52 thick at the panel, flat, rake 0. Coordinates x from the
left of the bounding square, y from the player's edge.

| Item | Value |
|---|---|
| Rings, outside in | TPU 85A tyre (equator 32 tall at r 150, top 44 at r 138); PETG rim band r 125–138, 46 rising to 53; PLA plate ⌀250 at 52; raised discs 2 mm proud (⌀90 under the stick, ⌀40 under each button) |
| Stick centre | (94, 134); shaft hole 21 (22 in the plate); M3 on the axes at 16; steel plate 53 × 95 pocket, 95 along x |
| Kick row (near) | LK (165, 120) · MK (205, 134) · HK (245, 128) — Sega arc, chosen by the owner 2026-09-12 |
| Punch row (far) | LP (157, 160) · MP (197, 174) · HP (237, 168) |
| Palm room | 104 in front of the kick index, 123 to the shaft |
| Brook | x 150–246, y 200–245, flat on the floor |
| LiPo | x 28–123, y 172–205, behind the stick body |
| ~~Qi coil~~ | ~~centre (185, 55), boss ⌀62, under the right palm, hole in the TPU ring~~ — removed by D-015 |
| Port board | 64-wide flat facet on the rear wall, x 133–163; the charging input (D-015). Tyre windowed over it (stage E) |
| Antenna bracket | front wall, x 116–124 |
| Underside | TPU 85A ring ⌀110–280, 6 thick, 25 % gyroid; thigh contact 247 / 224 / 180 per side at crest spacing 170 / 200 / 240 |
| Mass | about 2.0 kg estimated |
| Bed | single-nozzle mode at ⌀300 (325 × 320); ⌀296 if dual-nozzle |
| Livery | rim band carries the marquee lettering; tyre in the player colour (red P1/P4, blue P2, green P3); button discs in the punch/kick ramp; character inlay on the free plate face — **P1 art placed 2026-09-13:** Chun-Li poster (`../../cad/art/chunli.svg`), 45.7 × 64 mm, centred at (0, −84) in model coordinates (x from the disc centre, player at −y), i.e. the front band between the cluster and the rim; 4 mm to the LK and stick discs, 6.4 mm to the plate edge. Stage G (`../../cad/lap_disc_g.py`, same day) recesses a **50.1 × 68.4 mm pocket, 0.6 mm deep**, art plus `art_margin` 2.2 a side, centred at (0, −85): the slicer colours its floor black and the per-colour layers in `../../cad/art/layers/set4/` sit inside it (frame outer 49.8 × 68.2 at 64 mm art height). Corners clear the stick disc by 1.6 mm and the plate's flat by 1.9 mm, so the pocket cannot grow. The Fusion decal (`../../cad/lap_disc_art.py`) sits on the pocket floor as a visualisation |

CAD: `../../cad/lap_disc.py` (author script, fusion-design skill; bundle with
`python -m fusionhelper.bundle`, gate with `python -m fusionhelper.preflight`,
execute the `.bundled.py` through the Fusion MCP). Three stages, all built
and verified green on 2026-09-12 in the Fusion document "Arcade Controller
v1": `lap_disc.py` (shell, plate, panel holes, stiffener pocket),
`lap_disc_b.py` (rim slope, raised discs, tyre ridges, port boss and facet),
`lap_disc_c.py` (Brook standoffs on the ASSUMED 88 × 37 pitch, LiPo tray,
coil boss — since removed by stage F — antenna bracket, port window, TPU
ring and tyre as separate bodies). Stage D, `lap_disc_d.py`, built and verified green on 2026-09-13
in the same document (Fusion now reports it as "Arcade Controller v2", a
saved version, not a new file): four parametric edge fillets — `tyre_r`
10 on the tyre's two outer edges, `ring_r` 2.5 on the TPU ring's two
underside edges, `plate_r` 1 on the plate's top outer edge, `disc_r` 0.8 on
the seven raised discs. Stage E, `lap_disc_e.py`, same day: the port
facet had left a lens-shaped gap (3.8 mm at the centre) between the flat
and the round tyre, open from above; the tyre now fills that lens
(`tyre_fill`) and carries a `tyre_win_w` × `tyre_win_h` window
(`tyre_win_clear` 0.5 a side over the port window) so the port stays
reachable from outside — it is the charging input (owner, 2026-09-13; see
the open decision-log conflict with D-010 below). Not yet modelled:
port-board M3 holes (ASSUMED 24 × 20, wait for the measurement), the
rim-band lettering and the raised-disc colour split. Renders in
`cad/renders/`.

> **Settled the same day, D-015:** the rear port replaces Qi charging.
> Stage F, `lap_disc_f.py`, removed the stage C coil boss, rebuilt the TPU
> ring without its coil hole (re-rounded with `ring_r`) and deleted the five
> coil parameters. Verified green; shell underside back at z = 0.

> **Stage H, `lap_disc_h.py` (2026-09-13, owner's fit-out requests):**
> steel stiffener pocket corrected to **53 along x, 95 along y** (`stiff_w`,
> `stiff_d` swapped; it had been cut the other way round). **LiPo plinth**
> 4 mm tall (`plinth_h`) filling the tray floor, with two **zip-tie tunnels**
> 5 × 2 mm (`tie_w`, `tie_h`) through plinth and tray walls along y at
> `lipo_cx` ± 25 (`tie_dx`): a tie passes under the cell, up the outside of
> the tray wall, over the cell and back; use ties ≥ 200 mm. Cell top now
> 14 mm above the floor, 31 mm under the plate. **Five antenna cable hoops**
> on the floor against the inner wall at 30, 0, −30, −60 and −90° from +x
> (`hoop_ang_1..5`), 6 deep × 7 tall × 8 wide with a 3.5 × 4.5 opening
> (`hoop_*`), routing the pigtail from the Brook's corner round the +x side
> to the antenna bracket at −103°; opening ceiling is a 3.5 mm bridge,
> prints from the floor. **Port board mounting is still not modelled:** no
> hole positions or board type were ever recorded (only the ASSUMED
> 24 × 20), see the open item in `08-open-issues.md`.

Plan view: `../comfort-study/plan-outthere-circles.svg`. Full proposal:
`../comfort-study/design-3b-outthere-forms.md`. The 280 × 200 rectangle and
the 48/60 wedge above are superseded and kept for history.
