# 09 — Decision Log

Decisions already taken, with the reasoning. Read before proposing a change; if
new information contradicts one, say so explicitly rather than quietly editing.

---

**D-001 — Battery: 3.7 V 3700 mAh 103395 LiPo pouch, not 18650 cells**
*Date:* 2026-04-04 · *Status:* settled
The original brief listed 18650s. The pack actually purchased is the 103395
pouch (95 × 33 × 10 mm). Flat form factor suits a lap pad far better than a
cylindrical cell. All wiring and enclosure references use the pouch.

---

**D-002 — MT3608 boost converter removed from the build**
*Date:* 2026-04-04 · *Status:* settled
The Brook Gen 5W accepts 3.7 V nominal directly on its JST PH 2.0 mm battery
input. A 3.7 V → 5 V boost stage adds a component, heat, conversion loss and a
noise source for nothing. Battery connects to the Brook directly.
*Consequence:* the MT3608 already purchased is surplus.

---

**D-003 — Charging is Qi-only; USB-C for wired play and firmware only**
*Date:* 2026-04-04 · *Status:* **superseded by D-010 on 2026-09-06**
Adopted as a procedural workaround for two chargers on one cell. Not a
satisfactory end state. Retained here for history; do not build to it.

---

**D-004 — Console buttons use unique key codes (KEY_1–KEY_6), not BTN_START**
*Date:* 2026-04-04 · *Status:* settled
The `gpio-key` overlay instances feed one input stream. Four Start buttons all
emitting `BTN_START` (315) would be indistinguishable — no way to know which
player pressed Start. Unique key codes 2–7 give each button an identity that
RetroArch then maps per player.

---

**D-005 — Overlay is `gpio-key` (singular), buttons wired GPIO→GND**
*Date:* 2026-09-06 · *Status:* settled
Corrects two errors in the original guide (OI-003, OI-004). Active-low with the
SoC's internal pull-up. No external pull-down resistors.

---

**D-006 — `mk_arcade_joystick_rpi` not used**
*Date:* 2026-09-06 · *Status:* settled
Wrong tool for six system buttons with no stick; the common fork is stale and
its DKMS build is unreliable on current 64-bit Pi kernels. The `gpio-key`
overlay is sufficient.

---

**D-007 — Two-unit architecture: stationary Pi box + wireless lap pads**
*Date:* 2026-04-04 · *Status:* settled
Gameplay input on the pads, system input on the box. Keeps the pads identical
and simple, and means a flat pad battery never locks anyone out of the menus.
The Pi box needs no battery or Qi; the pads need no HDMI or ethernet.

---

**D-008 — Enclosures designed by the owner**
*Date:* 2026-04-04 · *Status:* **superseded by D-011 on 2026-09-06**
Three Bambu printers (X1 Carbon, H2C, H2D) and the owner does his own CAD.
Deliverables from Claude are dimensions, clearances and placement data — not
finished models. `Lap_Pad_Enclosure.scad` is reference geometry only.

---

**D-009 — Joystick and buttons stripped from an existing cabinet**
*Date:* 2026-04-04 · *Status:* settled
No new stick or buttons purchased. Ring out reused harnesses before trusting
their pinout — clone wiring varies.

---

**D-010 — One charger: Qi feeds the Brook's own USB-C input, TP4056 removed**
*Date:* 2026-09-06 · *Status:* adopted by the owner; build gated on the bench
test in `08-open-issues.md` OI-001
Resolves OI-001 by taking Fix A. The previous design wired a TP4056 and the
Brook Gen 5W's on-board charger to the same cell with no arbitration between
them. The TP4056 is removed entirely and the Qi receiver's 5 V is fed into the
Brook's USB-C input instead, leaving exactly one charging control loop on the
cell. OI-002 closes as a consequence: with no TP4056 there is no protection IC
left to bypass.

The owner's duty cycle (stated 2026-09-06) is what makes this cheap. A pad runs
from its cell while someone plays, then sits on the Qi plate to recharge. Play
and charge never overlap, and wired play over USB-C is explicitly not wanted.
So the loss of an externally reachable USB-C port costs nothing, and the slower
charge — roughly 8 hours at 500 mA rather than 4 hours at 1 A — is absorbed by
charging overnight between sessions.

*Consequences:*
- The TP4056 joins the MT3608 as surplus stock.
- The enclosure loses a 26 × 17 mm module, its two standoffs, and the 12 × 8 mm
  USB-C slot the SCAD reference puts on the front edge at x 145.
- The Qi feed needs a USB-C plug carrying R_p pull-ups on both CC lines; a bare
  5 V on VBUS is invisible to a compliant sink. See `03-wiring-lap-pad.md`.
- Runtime per charge is promoted from nice-to-know to a gating measurement: an
  8-hour recharge only works if one charge covers a whole evening.

*Fallback:* if the bench gate fails, Fix B (keep the TP4056, no USB-C cutout,
load moved to `OUT+/OUT−`) is the fallback and gets its own decision entry.

*Discussion artefact:* https://claude.ai/code/artifact/e27e12da-9b15-4990-a5b5-785cecda5941

---

**D-011 — Enclosure CAD moves to Claude, through FusionHelper**
*Date:* 2026-09-06 · *Status:* settled by the owner
Supersedes D-008. The owner has asked Claude to do the enclosure CAD rather than
supply dimensions for him to model. The work goes through the `fusion-design`
skill from the FusionHelper project, which enforces named parameters, named
datums, no raw coordinates, an offline preflight gate before any script reaches
Fusion, and a numeric verification block after it runs.

The skill is installed at `.claude/skills/fusion-design/` **relative to the repo
root** — that is `../.claude/skills/fusion-design/` from this docs tree, not
`docs/.claude/`. It is a copy; FusionHelper remains the source of truth (see
`VENDORED.md` beside it). Autodesk's own MCP server inside Fusion 360 is the
connection to the running application.

*What does not change:* the printers are still the owner's (H2C and H2D; print
lap pads on the H2D in single-nozzle mode, see `06-enclosure-reference.md`), and
the owner still reviews and owns the result.

*Consequence for `Lap_Pad_Enclosure.scad`:* it was reference geometry for a
workflow that no longer applies, and it is defective as geometry anyway. It
should be reduced to a parameter list or deleted once the Fusion model exists.
Pending the owner's call.

---

**D-012 — reserved**
*Status:* not yet written. The Lap Arcade Enclosure Study
(https://claude.ai/code/artifact/28289a89-8921-427e-a3c4-b8082337952b, §05
and §13) records an owner decision for dual-source charging — Qi plus a wired
side port, both fitted, one used at a time, no diode — that supersedes part of
D-010 and has not been written back here or to `CLAUDE.md`. Number held so the
study's references stay valid.

---

**D-013 — Lap pad grows to a 48 / 60 mm wedge; buttons and their wiring from the cabinet stay**
*Date:* 2026-09-12 · *Status:* settled by the owner
The buttons stripped from the cabinet (D-009) measure 40 mm from the panel
face to the bottom of the body, and about 50 mm with a straight
quick-disconnect fitted and the wire bent without strain. The enclosure
study's 26 / 46 mm saddle wedge had 28.5 mm of cavity at the kick row and its
own gate said anything over 35 mm would reopen the profile. Offered a taller
pad, low-profile replacement buttons (38 / 50, the floor set by the stick) or
flag connectors (42 / 54), the owner chose the taller pad with the existing
buttons and connectors: the alternatives saved 6–12 mm for a parts order no UK
arcade shop stocks or £55 of buttons, and were judged not worth it on a lap.

Profile becomes 48 mm at the front edge, 60 mm at the rear, flat underside,
3.4° panel rake. The R900 concave belly is deleted — it sat directly under the
left pair of buttons and had also been left out of the study's depth budget.
The two thigh contact ridges it provided come back as 3 mm TPU strips added to
the flat underside along both long edges; the Qi coil boss stands proud by the
same 3 mm so it stays flush with them and still keys into the dock pocket.

*Consequences:*
- D-009 stands; no new buttons, no new connectors.
- Shell height under the button cluster is 52.8–55.2 mm against a 52 mm
  minimum (50 fitted button + 2 floor).
- The stick bolts directly to the underside of the top plate with 4× M3 × 12 mm
  on holes 16 mm from the shaft centre at top, bottom, left and right (owner,
  same day); no plate drop. That cross pattern is not a Sanwa JLF's. Body
  measures 34 mm below the 1 mm steel stiffener plate, so 43.5 mm of shell is
  needed at the stick against 54 mm available.
- Dock bays widen to take a 48–60 mm pad; spine and pockets unchanged.
- `06-enclosure-reference.md` updated the same day. The SCAD file was already
  stale and is not updated.

*Discussion artefact:* https://claude.ai/code/artifact/28289a89-8921-427e-a3c4-b8082337952b

---

**D-014 — Lap pad form is a ⌀300 nested disc, 52 thick, flat; supersedes the 280 × 200 wedge**
*Date:* 2026-09-12 · *Status:* settled by the owner
The comfort study (`../comfort-study/`, study artefact §14) produced three
forms: a rectangular box with a rounded rim, a Star Trek TNG conn-station fan
(296 × 250), and a nested disc. The owner chose the disc, in Street Fighter
livery, and declined a foam mock-up on the grounds that a 280 mm rectangle had
already been accepted on the same lap.

Form: one ⌀300 disc, 52 thick at the panel, flat, rake 0, read as concentric
rings — TPU tyre at the edge, PETG rim band, ⌀250 removable PLA plate, raised
2 mm discs under the stick and each button. A TPU ring ⌀110–280 underneath is
the thigh contact. Stick at (94, 134); buttons on 40 pitch with the Sega arc,
index 14 mm nearer the player than middle and ring 6 mm nearer, chosen by the
owner over the template's straight rows (same day). Internals: Brook far right, LiPo behind the stick, Qi coil under
the right palm, port board in a rear flat facet. Dimensions in
`06-enclosure-reference.md`.

Why the disc over the box and the fan: longest thigh contact per side
(224 mm vs 142 for the triangle) with no width to mismatch, so the two-rail
rocking failure the lap-desk research describes cannot occur; free rotation
gives each player their hand angle; one rounded edge meets belly, thigh and
knee alike; 104 mm of palm room; mass centred in plan; fit margins of 9.5 mm
at the pinky nut and 13 mm at the stiffener; prints in either bed mode.

*Consequences:*
- D-013's profile (48/60 wedge) is superseded. Its 52-mm-under-every-button
  rule survives as the disc thickness. D-009 stands.
- Rake is 0. The wedge's anti-slide job goes to the TPU ring's friction.
- The dock's bays become round pockets; spine unchanged.
- The front-band art inlay goes: marquee lettering runs round the rim band,
  the tyre carries the player colour, button discs carry the punch/kick ramp,
  the character inlay sits on the free plate face.
- The H2D prints the ⌀300 shell in single-nozzle mode (325 × 320); ⌀296 if
  dual-nozzle is wanted for the rim lettering in one job.
- Mass about 2.0 kg estimated, the upper end of what fightstick users
  tolerate. Weigh the first shell.
- No round lap controller exists as a precedent. The first printed shell is
  the test.

*Discussion artefact:* https://claude.ai/code/artifact/28289a89-8921-427e-a3c4-b8082337952b (section 14)

---

**D-015 — Lap pads charge through a rear USB-C port; the Qi receiver is dropped**
*Date:* 2026-09-13 · *Status:* settled by the owner
The port board in the rear facet (D-014) is the charging input. The owner's
reason: fewer components and a simpler design. The Qi receiver module, the Qi
transmitter pads, the ⌀62 coil boss on the underside and the coil hole in the
TPU ring all go.

D-010's principle stands: exactly one charging control loop on the cell, the
Brook Gen 5W's own on-board charger. Only the source of its 5 V changes, from
the Qi receiver to a USB-C charger plugged into the rear port. The port board
must pass `VBUS`, `GND`, `CC1` and `CC2` through to the Brook's USB-C input so
the charger's own R_p advertisement reaches the Brook; a breakout that carries
only `VBUS` and `GND` needs the 56 kΩ pull-ups from D-010 fitted at the Brook
end instead. `[UNVERIFIED]` — which kind the purchased port board is.

*Consequences:*
- D-010's "no externally reachable USB-C port" is superseded. Wired play
  becomes physically possible; it is still not a design goal.
- OI-001's Qi-specific checks (receiver output, delivered current, coupling at
  an angle) are gone. The check that the Brook charges its attached cell from
  5 V on USB-C stays, and is now the ordinary use of the board.
- Charge current is whatever the Brook's charger draws from a wall charger,
  `[UNVERIFIED]`; the 500 mA / 8 h figure from D-010 was set by the Qi module
  and no longer applies.
- BOM: Qi receiver and transmitter become surplus; the 56 kΩ pull-ups are
  needed only if the port board lacks CC pass-through.
- CAD: stage E (`cad/lap_disc_e.py`, same day) fills the facet gap in the
  tyre and windows the tyre for the port. The coil boss and the ring's coil
  hole are to be removed from the model (stage F); `coil_x`, `coil_y`,
  `coil_boss_d`, `coil_boss_h`, `ring_coil_hole` go with them.
- `06-enclosure-reference.md`, `01`, `02`, `03`, `07`, `08` and `CLAUDE.md`
  updated the same day.

*Addendum, 2026-09-13 (same day):* the port board turned out to be Brook's
own panel-mount board B-C16046 — a USB **Type-B** socket plus a 3.5 mm jack on a
26.1 × 31 faceplate, with a 5-pin cable to the Brook's USB header — not a
USB-C breakout. Consequences: no CC lines and no pull-ups; charge through a
USB-C-to-B (or A-to-B) cable; the Brook sees plain 5 V on VBUS through its
own USB header. Mount modelled as stage I (`cad/lap_disc_i.py`). Where the
text above says USB-C for the port, read USB-B.

---

**D-016 — Lap pad is a bolted, serviceable assembly: ring, sled, plate, two TPU parts**
*Date:* 2026-09-13 · *Status:* settled by the owner
The owner wants the plate removable for repairs and upgrades with no
fasteners on its top face, the electronics reachable, and every printed part
free of unsupported overhangs. The shell is therefore split at the floor line
into a **ring** (walls, ledge, rim, port boss) and a **sled** (floor slab with
the Brook standoffs, LiPo tray and plinth, antenna cable hoops and antenna
bracket). Modelled as stage J (`cad/lap_disc_j.py`).

- **Plate** grows from 3.5 to 5 mm (`plate_t`); top face unchanged at 52. Six
  M3 heat-set inserts (4 mm hole, 4.2 deep, 0.8 mm skin) sit in its underside
  at r 116, angles 30/130/170/210/245/330°. Nothing hangs below the plate, so
  it prints top-up without support.
- **Plate to ring:** six 45° gussets rise from the wall to the plate seat, one
  per screw; the screw hole runs 13 mm down through the gusset to a ⌀7 spot
  face 9 mm below the seat. M3 × 16 socket screws from inside the cavity.
- **Ledge support:** a continuous 45° wedge under the ledge (an inside-corner
  chamfer, 17.6 mm each way, absent only at the port boss) so the ring prints
  open side up with no overhang. +119 cm³ ≈ 150 g PETG; pad estimate rises to
  about 2.2 kg.
- **Sled to ring:** six M3 × 12 from underneath, up through the TPU ring
  (⌀7 × 3.5 counterbores), the sled floor (⌀3.4) and into ⌀8 × 8 bosses on the
  ring's inner wall (2.5 mm pilots, 7 deep) at 55/115/185/235/285/345°. The
  same bolts clamp the TPU ring; nothing is glued.
- **Antenna bracket** moves from the front wall to 60° (rear-right), 22.7 mm
  from the nearest Brook standoff, so the 30 cm pigtail reaches with slack
  looped through the hoops. Hoops sit 0.4 mm off the wall so they belong to
  the sled.
- **Tyre:** top outer edge keeps the 10 mm fillet; bottom outer edge becomes a
  10 mm 45° chamfer so it prints flat. Its plug tunnel keeps a flat 23 mm top
  (TPU bridges poorly; cosmetic, inside the tunnel).
- **Venting:** none. The Brook's charger dissipates about 1 W; the button
  holes, stick hole and port tunnel breathe. Measure cell temperature on the
  first full charge.

*Consequences:* D-014's mass estimate becomes ~2.2 kg. BOM gains 6 × M3 × 16,
6 × M3 × 12, 6 × M3 × 4 heat-set inserts. `06-enclosure-reference.md` updated
the same day.
