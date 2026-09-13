# CLAUDE.md — Wireless RetroPie Lap Arcade

Context file for Claude Code. Read this first, then load only the `docs/` files
relevant to the task at hand.

## What this project is

A hardware build, not a software repo. Two physically separate units:

1. **Pi Console Box** — stationary, next to the projector. Raspberry Pi 4B
   running RetroPie, plus 6 arcade buttons wired directly to GPIO for system
   functions (Player 1–4 Start, Select, Hotkey). Drives the projector over HDMI.
2. **Wireless Lap Pad** (up to 4, one per player) — fully wireless, sits on the
   player's lap for beanbag gaming. Brook Gen 5W wireless fighting board,
   8-way joystick, 6× 30 mm action buttons, 3700 mAh LiPo, Qi charging.
   Bluetooth to the Pi.

Keep these as distinct design concerns. The Pi box needs no battery and no Qi.
The lap pads need no HDMI, ethernet or GPIO.

## Current phase

Planning / pre-assembly. Nothing is soldered yet. Most parts are bought
(see `docs/02-bom.md`).

The charging architecture is **decided** as of 2026-09-06: one charger, Qi into
the Brook's own USB-C input, TP4056 removed (D-010). The build is still gated on
a bench test — see `docs/08-open-issues.md` OI-001.

Enclosure CAD moved from the owner to Claude on 2026-09-06 (D-011); it is done
in Fusion 360 through the `fusion-design` skill.

The lap pad form was settled on 2026-09-12 as a ⌀300 nested disc, 52 mm thick,
flat, in Street Fighter livery (D-014), after a comfort study in
`docs/comfort-study/`. The reused cabinet stick and buttons (D-009) set the
thickness.

Remaining blockers: the OI-001 bench gate, JST PH 2.0 mm pigtails, a USB-C plug
breakout and 56 kΩ pull-ups, and the enclosure model itself.

## File map

| Path | What it is |
|---|---|
| `CLAUDE.md` | This file |
| `docs/README.md` | One-line index of the numbered docs |
| `docs/01-architecture.md` | System topology, signal and power flow |
| `docs/02-bom.md` | Bill of materials with purchase status |
| `docs/03-wiring-lap-pad.md` | Lap pad wiring, connector-by-connector |
| `docs/04-wiring-pi-console.md` | GPIO pinout and button wiring for the Pi box |
| `docs/05-retropie-config.md` | `config.txt`, overlays, RetroArch, Bluetooth pairing |
| `docs/06-enclosure-reference.md` | Component dimensions and placement for CAD |
| `docs/07-testing.md` | Bring-up and acceptance checklist |
| `docs/08-open-issues.md` | Unresolved problems and things needing verification |
| `docs/09-decision-log.md` | Decisions made, with rationale — read before changing anything |
| `Wireless_Arcade_Build_Guide.md` | Earlier long-form guide. **Superseded**; contains known errors listed in `08-open-issues.md`. Do not treat as authoritative. |
| `Arcade_Project_Dashboard.html` | Earlier status dashboard. Same caveat. |
| `Lap_Pad_Enclosure.scad` | OpenSCAD reference geometry. Reference only — see below. |
| `STEP_Reference_Files/` | STEP models of components for CAD fit checks |
| `../.claude/skills/fusion-design/` | Fusion 360 CAD skill used for the enclosures (D-011). Path is relative to the repo root, one level above this file. |

## Ground rules for working on this project

- **Enclosure CAD is yours, through the `fusion-design` skill.** D-011
  superseded D-008 on 2026-09-06: the owner asked Claude to model the
  enclosures rather than be handed dimensions to model himself. Work through
  `../.claude/skills/fusion-design/`, which enforces named parameters, named
  datums, no raw coordinates, an offline preflight gate before any script
  reaches Fusion, and a numeric verification block after it runs. The printers
  are still the owner's (X1 Carbon, H2C, H2D; lap pads print on the H2D in
  single-nozzle mode) and he still reviews and owns the result. The `.scad`
  file is stale reference only — see `docs/06-enclosure-reference.md`.
- **Do not silently change a decision in `09-decision-log.md`.** If new
  information contradicts one, say so and explain why; don't just edit.
- **Flag unverified claims.** Several component behaviours (Brook Gen 5W
  charging behaviour, OLED interface, protection-circuit topology) are assumed
  from documentation rather than measured. Anything marked `[UNVERIFIED]` in
  the docs must not be presented as fact.
- **Polarity and charging safety are load-bearing.** Reversed polarity kills the
  Brook board. Any change to the power chain gets called out explicitly, not
  buried in a diff. D-010 leaves exactly one charger on the cell; do not
  reintroduce a second one without a new decision entry.
- **Duty cycle:** a pad runs from its cell while someone plays, then recharges on
  the Qi plate. Play and charge never overlap. Wired play is not wanted, so lap
  pads have no externally reachable USB-C port.
- Units are millimetres and volts. UK suppliers preferred; AliExpress excluded.

## Conventions

- Docs are Markdown, one concern per file, numbered for reading order.
- Statuses in the BOM: `PURCHASED` / `HAVE` (already owned, e.g. stripped from
  an existing cabinet) / `NEEDED` / `NOT NEEDED` (deliberately designed out).
- Anything time-sensitive gets an absolute date, not "recently".
