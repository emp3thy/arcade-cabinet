# 03 — Lap Pad Wiring

Charging topology settled 2026-09-06 by **D-010** (Fix A) and revised
2026-09-13 by **D-015**. One charger: a USB-C port board in the rear rim feeds
the Brook's own USB-C input, and the TP4056 is not fitted. The Qi receiver
D-010 used as the 5 V source is dropped.

**The power chain is still gated on a bench test.** Do not solder sections 1–3
until the checks in `08-open-issues.md` OI-001 pass on one pad.

## Power chain overview

```
[USB-C charger] ──cable──> [USB-C port board, rear rim]
                                     │
                                     │  VBUS + GND + CC1 + CC2 passed through
                                     ▼
                            [USB-C plug] ──> [Brook USB-C input]
                                                      │
                                            [Brook on-board charger]
                                                      │  JST PH 2.0 mm
                                                      ▼
                                             [LiPo 103395, 3.7 V]
                                                      │
                                             [Brook logic + BT]
```

One charging control loop, on one cell. No TP4056, no boost converter. The
rear port is the pad's only external connector.

## 1. Port board → Brook USB header

The port board is Brook's panel-mount B-C16046 (2026-09-13): a USB **Type-B**
socket and a 3.5 mm jack on the faceplate, with the supplied 5-pin cable to
the Brook's USB header. No wiring to do: plug the cable in. USB-B has no CC
lines, so nothing below about R_p applies to this board; a USB-C charger
reaches it through a C-to-B cable, whose plug carries the required pull-down.

The R_p notes are kept for the case of a USB-C breakout being substituted:

**Then the pull-ups are not optional.** A bare 5 V on `VBUS` with floating CC pins is
invisible to a compliant USB-C sink. A *source* advertises its current capability
with R_p, a pull-**up** to 5 V, one resistor per CC line, both the same value:

| R_p | Advertises |
|---|---|
| 56 kΩ | Default USB — 500 mA |
| 22 kΩ | 1.5 A |
| 10 kΩ | 3 A |

Use **56 kΩ** in that case. Do not advertise more than the charger can deliver;
22 kΩ only with a charger rated for 1.5 A.

Do **not** fit 5.1 kΩ anywhere in this harness. 5.1 kΩ to ground is R_d, the
pull-**down** a *sink* presents. The Brook already has it. Fitting your own would
be wrong in value, direction and role.

## 2. TP4056 — not fitted

Removed by D-010. The purchased modules are surplus; keep them for the parts bin
alongside the MT3608.

If the OI-001 bench gate fails and you fall back to Fix B, the TP4056 goes back
in and the Brook must be run from `OUT+/OUT−`, not `BAT+/BAT−`, so the DW01 sees
the load. Do not simply revert this file — write the fallback up as its own
decision entry first.

## 3. Battery → Brook Gen 5W

The Brook has a JST PH 2.0 mm battery input.

- Re-terminate the LiPo leads with a JST PH 2.0 mm plug, or use a pigtail and
  crimp/solder to the pack leads with heatshrink.
- **Polarity check with a multimeter before first connection.** Reversed
  polarity permanently destroys the board. The connector housing will let you
  insert it either way if you crimp it wrong.

| From | To |
|---|---|
| Battery + | Brook `BAT+` (red) |
| Battery − | Brook `BAT-` (black) |

## 4. Joystick → Brook

Four microswitches, common ground.

| Joystick | Brook terminal |
|---|---|
| UP | `UP` |
| DOWN | `DOWN` |
| LEFT | `LEFT` |
| RIGHT | `RIGHT` |
| Common | `GND` |

A JLF's 5-pin harness carries the four directions plus common. If reusing a
harness from the old cabinet, ring it out first — clone pinouts vary.

## 5. Buttons → Brook

Six 30 mm buttons, each switching its Brook input to ground.

> `P1`–`P6` below are **Brook button-input terminals on one pad**, not players.
> Player 1–4 live on the Pi console box (`04-wiring-pi-console.md`). All four
> pads are wired identically; player identity comes from Bluetooth pairing
> order, not from wiring.

| Button | Brook terminal |
|---|---|
| 1 | `P1` |
| 2 | `P2` |
| 3 | `P3` |
| 4 | `P4` |
| 5 | `P5` |
| 6 | `P6` |
| all commons | `GND` (daisy-chain a ground rail) |

Daisy-chaining the ground side with quick-disconnects makes the top plate
removable in one piece. Worth doing — you will open these pads again.

## 6. OLED → Brook

`[UNVERIFIED]` — confirm the Brook's display header pinout and voltage against
the board revision you have before connecting.

| OLED | Brook |
|---|---|
| SDA | I²C `SDA` |
| SCL | I²C `SCL` |
| VCC | 3.3 V or 5 V — **check the module's rating first** |
| GND | `GND` |

## Charging — no operational rule required

The earlier design needed a written rule ("charge over Qi only, never plug USB-C
at the same time") because two chargers sat on one cell. D-010 removes the second
charger, so the rule is gone with it. There is nothing to remember and nothing a
user can do wrong, which was the point.

Duty cycle: the pad runs from its cell while someone plays, then charges from a
USB-C charger through the rear port (D-015). Charge time depends on what the
Brook's charger draws from a wall charger, `[UNVERIFIED]`; measure it (OI-010).

**The rear port is the only cutout.** It reaches the Brook's USB-C input, so
firmware updates no longer mean opening the pad.
