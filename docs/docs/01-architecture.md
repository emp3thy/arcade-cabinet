# 01 — Architecture

## Topology

```
                         ┌──────────────────────────┐
                         │       PROJECTOR          │
                         └────────────▲─────────────┘
                                      │ HDMI
                         ┌────────────┴─────────────┐
                         │    PI CONSOLE BOX        │
                         │  Raspberry Pi 4B         │
                         │  RetroPie                │
                         │                          │
                         │  GPIO buttons:           │
                         │   P1–P4 Start, Select,   │
                         │   Hotkey                 │
                         └────────────▲─────────────┘
                                      │ Bluetooth (Brook Gen 5W)
             ┌────────────┬───────────┴───────────┬────────────┐
             │            │                       │            │
       ┌─────┴────┐ ┌─────┴────┐            ┌─────┴────┐ ┌─────┴────┐
       │ LAP PAD 1│ │ LAP PAD 2│            │ LAP PAD 3│ │ LAP PAD 4│
       └──────────┘ └──────────┘            └──────────┘ └──────────┘
       (identical, one per player, charged on Qi pads between sessions)
```

## Why the split

Players sit on beanbags several metres from the Pi. Anything tethered defeats
the point. So:

- All *gameplay* input (stick + 6 buttons) lives on the wireless pad.
- All *system* input (Start, Select, Hotkey) lives on the box next to the Pi,
  wired straight to GPIO. This keeps the pads simple and identical, and means
  a flat pad battery never locks anyone out of the menus.

## Lap pad internal blocks

```
[Qi Rx coil] ──5V + R_p on CC──> [Brook USB-C in]
                                        │
                                 [Brook on-board charger]
                                        │ JST PH 2.0mm, 3.7V
                                        ▼
                              [3700 mAh LiPo 3.7V]
                                        │
[Joystick 4 sw] ──────────────> [Brook Gen 5W] ──BT──> Pi
[6× buttons]    ──────────────>       │
                                      ▼
                                 [OLED status]
```

No boost converter. The Brook Gen 5W takes 3.7 V nominal directly — see
`09-decision-log.md` D-002.

No TP4056 either. The Qi receiver feeds the Brook's own charger, so exactly one
charging control loop sits on the cell — see D-010. The earlier design put a
TP4056 and the Brook's charger on the same cell with no arbitration between
them; that is resolved, and the operational rule it needed is gone with it.

Duty cycle: play from the cell, then recharge on the Qi plate. The two never
overlap. There is no externally reachable USB-C port on a lap pad.

> **Still gated.** The power chain is not buildable until the bench checks in
> `08-open-issues.md` OI-001 pass on one pad.

## Pi console box internal blocks

```
[6–8 arcade buttons] ──> [Pi 4B GPIO] ──> gpio-key overlay
                                              │
                                              ▼
                                     Linux input events
                                              │
                                              ▼
                            EmulationStation / RetroArch bindings
```

No encoder board. Buttons go straight to GPIO pins. See `04-wiring-pi-console.md`.
