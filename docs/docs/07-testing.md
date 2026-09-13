# 07 — Bring-up and Testing

Work top to bottom. Do not skip the power-chain section — it is the only part
that can destroy hardware or start a fire.

## A. Power chain — the D-010 gate, on one pad, before building four

Do this on a bench with a supply and a current meter, not on a beanbag. The
whole charging design rests on the first two checks.

- [ ] Bench supply at 5 V into the Brook's USB-C input, cell attached, meter in
      line. Does it charge with bare `VBUS` and floating CC pins? Record the
      current.
- [ ] If not, fit 56 kΩ R_p from 5 V to each of `CC1` and `CC2` and retry.
      Record the current it settles at.
- [ ] Does it still charge with no USB host attached? The Qi feed carries power
      and no data.
- [ ] What mode does the board enter when it sees `VBUS`? If it drops to wired
      controller mode that is harmless here, since nobody plays a pad on the
      plate, but record it so it is not mistaken for a fault later.
- [ ] Qi transmitter powered, receiver on it: measure receiver output. Expect
      ~5 V. Record the actual figure **and its delivered current under load** —
      this is what limits the R_p choice, not the charge time you would like.
- [ ] Full chain, Qi through to the cell: battery terminal voltage after charge
      is 4.15–4.2 V.
- [ ] Time from flat, measured. Expect roughly 8 hours at 500 mA. If it is much
      worse, the Qi module is the suspect.
- [ ] Battery holds ≥4.0 V after 30 minutes off charge.
- [ ] Nothing in the chain gets warm enough to be uncomfortable to touch.

If the first two checks fail, stop and fall back to Fix B — see OI-001. Do not
improvise a third topology at the bench.

## B. Brook Gen 5W, powered

- [ ] **Polarity verified with a multimeter at the JST plug before insertion.**
- [ ] Board powers up from battery — status LED lights.
- [ ] All four stick directions register.
- [ ] All six buttons register.
- [ ] OLED shows something sensible.
- [ ] Bluetooth pairs with the Pi.
- [ ] Usable at 4 m — the actual beanbag-to-Pi distance, not a bench test.
- [ ] Runtime under continuous play: record hours to first low-battery warning.

## C. Charging safety

Under D-010 there is one charger and no external port, so the old dual-charger
test is gone. What remains:

- [ ] Cell temperature through a full charge cycle. Warm is fine, hot is not.
- [ ] Charge terminates. Leave it on the plate past the expected finish time and
      confirm the cell settles rather than climbing past 4.2 V.
- [ ] Pad on the plate at an angle, and offset from the coil centre: it either
      charges or it does not, with no sustained half-coupled state getting warm.
- [ ] Over-discharge: play a pad to cutoff and confirm something stops it. With
      the TP4056 gone, this is the pack's own protection board or the Brook's
      management, and it is the one safety function nobody has verified. See
      OI-002.

## D. Pi console box

- [ ] `dtoverlay -h gpio-key` confirms the overlay exists on this image.
- [ ] After adding config lines and rebooting, `/proc/bus/input/devices` lists
      six devices with the expected labels.
- [ ] `evtest` shows one clean press/release per button — no bounce, no
      phantom repeats.
- [ ] Pi boots normally with all overlays loaded (a bad overlay line can stop
      boot — keep a spare SD card image).

## E. Integration

- [ ] Each pad appears as its own `/dev/input/jsX`.
- [ ] `jstest` shows correct axes and buttons per pad.
- [ ] EmulationStation menu navigation works from a pad.
- [ ] Console box Select and Hotkey work in EmulationStation.
- [ ] In-game: player 1 stick+buttons from the pad, Start from the console box,
      **on the same player slot**. This is the risky integration point — see
      `05-retropie-config.md`.
- [ ] Hotkey → exit game works.
- [ ] Four pads simultaneously in a 4-player game, correct player assignment.
- [ ] Bluetooth stable over a 30-minute session with four pads connected —
      no dropouts, no input lag.
- [ ] Config survives a reboot.

## F. Soak

- [ ] One full evening of real use with the people who will actually use it.
      Note every annoyance, however small; that list is the v2 backlog.
