# 08 — Open Issues

Unresolved problems, contradictions in the existing material, and claims that
have been assumed rather than verified. Ordered roughly by how much damage they
can do.

---

## OI-001 — Two chargers on one cell (DECIDED 2026-09-06 — Fix A, build gated on a bench test)

**Decision.** Fix A is adopted. See `09-decision-log.md` D-010. The TP4056 comes
out; the Qi receiver's 5 V goes into the Brook's USB-C input; one charger remains
on the cell. OI-002 closes as a consequence.

**Still gating the build.** Do not solder the power chain until the bench test
below passes on one pad:

- [ ] The Brook charges its attached battery from an external 5 V source on
      USB-C. Bench supply, current meter in line, cell attached. Try bare
      `VBUS` first — many devices charge without CC negotiation. If it does
      not, fit 56 kΩ R_p pull-ups and retry.
- [ ] It still charges with `VBUS` present and no USB host attached. The Qi
      feed carries power and no data. If the board drops into wired controller
      mode on seeing `VBUS`, that is harmless under the owner's duty cycle —
      nobody plays a pad sitting on the plate — but record the behaviour.
- [ ] The Qi receiver's actual delivered current under load, measured rather
      than read off the listing. This sets the R_p value and the honest charge
      time.

If the gate fails, fall back to Fix B below and move the load to `OUT+/OUT−`.

The original statement of the problem is kept below for history.

---

## OI-001 (original statement) — Two chargers on one cell

**Problem.** The design hard-wires a TP4056 to the LiPo *and* relies on the Brook
Gen 5W's own USB-C charging circuit on the same cell. Two independent chargers
with independent CC/CV control loops sharing one battery is not a supported
configuration. Failure modes: current fighting, overcharge past 4.2 V, heat,
cell damage, worst case thermal runaway on a pouch cell sitting on someone's lap.

**Current mitigation.** A written rule: "charge over Qi, never plug USB-C while
on the pad." This is a procedure, not a design. Four pads, several people, a
dark room and beer — the procedure will be violated.

**Candidate fix A — drop the TP4056.** Feed the Qi receiver's 5 V straight into
the Brook's USB-C input (via a USB-C breakout or a short pigtail). One charger,
one control loop, one less module in the pad, no protection-bypass question
(OI-002 disappears too). Depends on the Brook charging its attached battery from
USB-C regardless of power source, which is `[UNVERIFIED]` — but is exactly what
the board does when you plug a charger into it on a desk.

**Candidate fix B — keep the TP4056, physically block USB-C.** No USB-C cutout in
the enclosure at all; the port is only reachable by opening the pad for a
firmware update. Preserves the current wiring, costs you convenient wired play.

**Recommendation.** Fix A, subject to verifying the Brook's USB-C charging
behaviour on the bench with a bench supply and a current meter. It removes a
component, a failure mode and a rule to remember. Fix B is the safe fallback if
verification fails.

**Adopted 2026-09-06.** The owner confirmed the duty cycle — play on the cell,
recharge on the plate afterwards, no wired play wanted — which removes Fix A's
only cost. Fix A taken. See the decision block at the top of this issue.

An earlier draft of Fix A proposed OR'ing the Qi feed and the external port with
Schottky diodes so wired play survived. That circuit is dropped: there is no
wired play to preserve, so there is no second source and no diode.

---

## OI-002 — TP4056 protection is bypassed (CLOSES WITH D-010)

**Closes as a consequence of OI-001 Fix A.** With the TP4056 removed there is no
DW01 to bypass, and the cell's only protection is whatever the pack and the
Brook provide. That makes the question below more important, not less — it is
now the pad's only over-discharge defence.

- [ ] Confirm whether the 103395 pack has its own integrated protection board.
      Look under the kapton at the lead end.

If the bench gate fails and Fix B is built instead, this issue reopens in full
and the Brook must be run from `OUT+/OUT−`.

Terminal naming: `OUT+/OUT−` and `BAT+/BAT−` here are TP4056 module terminals.
The Brook's own battery header is also labelled `BAT+/BAT−` — see
`03-wiring-lap-pad.md` §3.

The original statement follows.

---

## OI-002 (original statement) — TP4056 protection is bypassed

The protection IC on a "TP4056 with protection" module sits between the `BAT`
terminals and the `OUT` terminals. Loads must draw from `OUT+/OUT−` to get
over-discharge and short-circuit protection.

The current wiring runs the Brook from the battery / `BAT` side. That means the
DW01's over-discharge cutoff never sees the load. The cell's only protection is
whatever the Brook's own battery management does — `[UNVERIFIED]`, and possibly
nothing beyond a low-voltage warning.

Options: (a) run the Brook from `OUT+/OUT−`; (b) confirm the LiPo pack has its
own integrated PCM (many 103395 packs do — check for a small board under the
kapton at the lead end); (c) resolved automatically if OI-001 fix A is adopted.

---

## OI-003 — GPIO overlay name is wrong in the old guide (RESOLVED in docs, not yet on hardware)

`Wireless_Arcade_Build_Guide.md` and the dashboard specify
`dtoverlay=gpio-keys`. The parameterised Raspberry Pi overlay taking
`gpio=` / `keycode=` / `label=` is **`gpio-key`**, singular. As written those
lines silently fail to load and no buttons appear.

Corrected in `05-retropie-config.md`. Confirm on the actual image with
`dtoverlay -h gpio-key`.

---

## OI-004 — Button wiring contradicts the overlay defaults (RESOLVED in docs)

The old guide wires console buttons from **+3.3 V to GPIO** with 10 kΩ
pull-downs, while printing a `gpio-key` config that defaults to active-low with
an internal pull-up. The two halves of that page cannot both be right.

`04-wiring-pi-console.md` standardises on button-to-GND, overlay defaults, no
external resistors. The 10 kΩ resistors already purchased are surplus.

---

## OI-005 — Keyboard Start + joypad stick on one player slot (OPEN, needs test)

Player 1's stick and buttons come from a Bluetooth joypad; Player 1's Start comes
from a keyboard-type device on the Pi. RetroArch keeps keyboard and joypad binds
separately per player, so this should work — but it is untested here, and
EmulationStation's input model is not RetroArch's.

Test this before finalising the console box layout. If it fails, the fallback is
a 7th button on each lap pad for Start, which changes the pad panel design.

---

## OI-006 — Lap pad exceeds X1 Carbon build volume (RESOLVED 2026-09-06)

The 300 mm reference width does not fit the X1 Carbon's 256 mm bed. Resolved by
printing lap pads on the **H2D in single-nozzle mode** (325 mm X, 25 mm of
headroom). The part is not split and not shrunk. The H2C would work
single-nozzle with 2.5 mm a side, which is inside brim and warp noise, and does
not fit at all in dual-nozzle mode. See `06-enclosure-reference.md`.

---

## OI-007 — Brook footprint ambiguity (OPEN, trivial)

Two conflicting STEP models: 96 × 45 (marked VERIFIED) and 97 × 52. The SCAD
reference uses 97 × 52. Measure the actual board and delete the wrong file.

---

## OI-008 — Charge time claim is wrong (RESOLVED in docs)

The old guide claims a 2–3 hour full charge. A stock TP4056 charges at ~1 A;
3700 mAh from flat is ~4 hours plus CV tail. Corrected in `07-testing.md`.

**Superseded again by D-010.** With the TP4056 gone and charging at 500 mA
through the Brook, expect roughly 8 hours from flat. Neither the 2–3 hour claim
nor the 4 hour figure applies to the current design.

---

## OI-009 — Unverified component behaviour (OPEN)

Everything marked `[UNVERIFIED]` in the docs, collected:

- Brook Gen 5W USB-C charging behaviour with an attached battery **(now gates
  the D-010 build — see OI-001)**
- Whether it charges with `VBUS` present and no USB host, and what mode it
  enters when it sees `VBUS`
- The Qi receiver module's real delivered current under load
- Brook display-header pinout and voltage; what the OLED actually reports
- Whether the 103395 pack has an integrated protection circuit **(now the pad's
  only over-discharge protection under D-010)**
- Whether four identical Brook pads can be given distinct Bluetooth names
- Brook display/input mode required for clean Linux enumeration

These are bench tests, not research tasks. Do them with one pad before
duplicating anything four times.

---

## OI-010 — Runtime per charge is now a gating number (OPEN)

D-010 accepts a recharge of roughly 8 hours at 500 mA. That only works if a
single charge covers a whole evening of play. Measure hours to first low-battery
warning under continuous use early, not at the end of the build. If one charge
does not cover a session, the answer is a higher R_p (and a Qi module that can
actually supply it), not a return to the TP4056.
