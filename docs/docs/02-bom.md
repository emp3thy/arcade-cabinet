# 02 — Bill of Materials

Status key: `PURCHASED` · `HAVE` (already owned) · `NEEDED` · `NOT NEEDED`
(deliberately designed out — do not re-add without reading the decision log).

Inventory last confirmed **2026-04-04**; statuses revised **2026-09-06** for
D-010 (TP4056 out) and D-011 (enclosure CAD moves to Fusion). Verify before
ordering.

## Lap pad — per controller

| Role | Part | Status |
|---|---|---|
| Wireless encoder | Brook Gen 5W Wireless Fighting Board | PURCHASED |
| Battery | 3.7 V 3700 mAh LiPo pack, 103395 (95×33×10 mm) | PURCHASED |
| ~~Wireless charge Rx~~ | ~~Qi receiver module, 5 V output, ~50 mm coil~~ | **NOT NEEDED** (D-015) — purchased, now surplus |
| Status display | Small OLED for Brook Gen 5W | PURCHASED |
| Joystick | 8-way, Sanwa JLF or clone — stripped from existing cabinet | HAVE |
| Action buttons | 6 × 30 mm arcade pushbuttons — stripped from existing cabinet | HAVE |
| Wiring | Wire, crimps, quick-disconnect harness | HAVE |
| Battery connector | JST PH 2.0 mm pigtail (Brook battery input) | **NEEDED** |
| Charge port | USB-C port board in the rear rim, ~30 × 26 mm, wired to the Brook's USB-C input with `VBUS`, `GND`, `CC1`, `CC2` (D-015) | status **UNCONFIRMED** — the enclosure window is cut to 30.4 × 26.4; confirm the board and whether it passes CC through |
| CC pull-ups | 2 × 56 kΩ resistors per pad | **NEEDED only if the port board does not pass CC through** (D-015) |
| Enclosure | 3D printed; Fusion CAD by Claude, owner reviews and prints (D-011) | **NEEDED** |
| Charger | TP4056 module with DW01 protection | **NOT NEEDED** (D-010) — purchased, now surplus |
| Boost converter | MT3608 3.7 V → 5 V | **NOT NEEDED** (D-002) |

## Charging station

| Role | Part | Status |
|---|---|---|
| ~~Qi transmitter pad~~ | ~~One per charging position~~ | **NOT NEEDED** (D-015) — purchased, now surplus |

## Pi console box

| Role | Part | Status |
|---|---|---|
| Console | Raspberry Pi 4 Model B | HAVE |
| System buttons | 6 arcade pushbuttons (P1–P4 Start, Select, Hotkey) | HAVE |
| Wiring | Wire, Dupont connectors | HAVE |
| Pull-down resistors | 10 kΩ | **NOT NEEDED** (D-005) — purchased, now surplus |
| USB-C panel mount (optional — tidiness, not function) | Clean external power access to the Pi | NEEDED |
| Enclosure | Fusion CAD by Claude, owner reviews and prints (D-011) | **NEEDED** |

## Notes

- The original project brief listed 18650 cells. That is superseded — the
  purchased battery is the 103395 pouch pack (D-001).
- The LiPo pack almost certainly ships with a plug that is *not* JST PH 2.0 mm.
  Buy pigtails; do not cut and twist.
- Nothing in this BOM covers a low-battery indicator beyond whatever the Brook's
  OLED reports. `[UNVERIFIED]` — confirm what the OLED actually displays.
- The 56 kΩ CC pull-ups are **not** the 10 kΩ pull-downs already purchased for
  the Pi console box, and they are not the 5.1 kΩ R_d a sink presents. Different
  value, different role. See `03-wiring-lap-pad.md`.
- Three modules are now surplus per pad: the MT3608 (D-002), the TP4056
  (D-010) and the Qi receiver (D-015), plus the Qi transmitter pads. Do not
  re-add any without reading the decision log.
- In the Pi console box the 10 kΩ pull-downs are surplus too (D-005): the
  buttons wire GPIO→GND and the overlay uses the SoC's internal pull-up.
