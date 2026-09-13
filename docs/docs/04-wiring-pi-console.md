# 04 — Pi Console Box Wiring

Six system buttons wired directly to Pi 4B GPIO. No encoder board.

## Pin assignment

| Function | GPIO (BCM) | Physical pin |
|---|---|---|
| Player 1 Start | GPIO17 | 11 |
| Player 2 Start | GPIO27 | 13 |
| Player 3 Start | GPIO22 | 15 |
| Player 4 Start | GPIO23 | 16 |
| Select | GPIO24 | 18 |
| Hotkey | GPIO25 | 22 |
| Ground | GND | 6, 9, 14, 20, 25, 30, 34, 39 |

None of these pins clash with the Pi's I²C, SPI or UART defaults.

## Wiring: button to GND, not to 3.3 V

```
GPIO pin ───[ button ]─── GND
```

Each button shorts its GPIO pin to ground when pressed. Nothing else. No
external resistors, no 3.3 V rail.

This is **active-low** wiring, and it is what the `gpio-key` device-tree overlay
expects by default (`active_low=1`, `gpio_pull=up` — the SoC's internal pull-up
holds the line high when the button is open).

> The earlier build guide showed buttons wired from **+3.3 V** to GPIO with
> 10 kΩ pull-downs. That is the opposite convention and does not match the
> overlay config it printed alongside. Use the wiring on this page. The 10 kΩ
> resistors you bought are not needed; keep them for the parts bin.

## Practical build notes

- Common ground rail: one wire from a GND pin to a small bus (a strip of
  Dupont-crimped splices or a scrap of stripboard), then one wire per button.
- Use crimped Dupont connectors at the Pi header, not soldered wires — you will
  want to unplug the header to get the Pi out of the box.
- Label every wire at both ends. Six unlabelled black wires is a bad afternoon.
- Debounce is handled in software by the overlay (`debounce` parameter,
  default 50 ms). No RC networks required.

## Enclosure implications

The box must leave accessible: HDMI (to projector), USB-C power, and ideally
ethernet and two USB-A ports. A panel-mount USB-C extension makes the power
inlet tidy. See `06-enclosure-reference.md`.
