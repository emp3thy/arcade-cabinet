# 05 — RetroPie Configuration

Target: Raspberry Pi 4B, RetroPie on Raspberry Pi OS (Bookworm-era). Adjust the
config file path if your image differs — on recent images it is
`/boot/firmware/config.txt`, on older ones `/boot/config.txt`.

## GPIO buttons: `gpio-key` overlay

One overlay instance per button. Each creates its own input device emitting a
single key event.

```
# --- Arcade console box system buttons ---
dtoverlay=gpio-key,gpio=17,keycode=2,label="P1_START"
dtoverlay=gpio-key,gpio=27,keycode=3,label="P2_START"
dtoverlay=gpio-key,gpio=22,keycode=4,label="P3_START"
dtoverlay=gpio-key,gpio=23,keycode=5,label="P4_START"
dtoverlay=gpio-key,gpio=24,keycode=6,label="SELECT"
dtoverlay=gpio-key,gpio=25,keycode=7,label="HOTKEY"
```

Two things to get right:

1. **The overlay is `gpio-key`, singular.** `gpio-keys` is the underlying Linux
   driver name, not the parameterised Raspberry Pi overlay that accepts
   `gpio=` / `keycode=` / `label=`. Earlier notes in this project used
   `gpio-keys`; those lines will not load. Verify with
   `dtoverlay -h gpio-key` on the Pi.
2. **Defaults are active-low with an internal pull-up**, which matches the
   button-to-GND wiring in `04-wiring-pi-console.md`. Don't add `active_low=0`.

### Key codes used

| Key | Code | Assigned to |
|---|---|---|
| `KEY_1` | 2 | Player 1 Start |
| `KEY_2` | 3 | Player 2 Start |
| `KEY_3` | 4 | Player 3 Start |
| `KEY_4` | 5 | Player 4 Start |
| `KEY_5` | 6 | Select |
| `KEY_6` | 7 | Hotkey |

**Why not `BTN_START` (315) for all four?** Because the four Start buttons would
be indistinguishable — same event, same device, no way to tell which player
pressed it. Unique keyboard codes give each button its own identity, which is
then mapped per player in RetroArch. (D-004)

### Verifying

```bash
# after reboot — should list six new devices with your labels
cat /proc/bus/input/devices | grep -A4 -i start

# watch events from one of them
sudo evtest        # pick the device, press the button
```

## RetroArch: mapping the console buttons to players

Edit `/opt/retropie/configs/all/retroarch.cfg`:

```
input_player1_start = "num1"
input_player2_start = "num2"
input_player3_start = "num3"
input_player4_start = "num4"
input_player1_select = "num5"

input_enable_hotkey = "num6"
input_exit_emulator = "num6"      # hotkey alone, or pair with a pad button
```

`[UNVERIFIED]` — mixing a keyboard-device Start with a joypad-device stick/buttons
for the *same* player slot is supported by RetroArch in principle (keyboard and
joypad binds are independent), but has not been tested on this setup. Test it
early; if it misbehaves, the fallback is to put Start on the lap pads and use the
console box buttons only for coin/menu functions.

## EmulationStation

ES reads keyboard input for menu navigation with its own bindings
(`/opt/retropie/configs/all/emulationstation/es_input.cfg`). Once the Brook pads
are paired, ES will normally be driven from a pad; the console box Select and
Hotkey buttons are the fallback for when every pad is flat.

## Brook Gen 5W Bluetooth pairing

1. Hold the pairing button on the Brook board ~3 s. LED flashes rapidly.
2. On the Pi: **RetroPie Setup → Configuration/Tools → bluetooth →
   Register and Connect to Bluetooth Device**.
3. Select the Brook from the scan list, confirm.
4. LED goes steady / slow pulse when connected.
5. In EmulationStation: **Start → Configure Input**, map stick and buttons.

Set **Display Mode: 3 (or as documented for the board) / D-input** if the pad is
not recognised — the Brook's mode affects how it enumerates. `[UNVERIFIED]`
against the firmware revision on hand.

### Multiple pads

```
input_player1_joypad_index = "0"
input_player2_joypad_index = "1"
input_player3_joypad_index = "2"
input_player4_joypad_index = "3"
```

Indices follow connection order, so they shuffle depending on which pad powers on
first. Check with `ls /dev/input/js*` and `jstest /dev/input/js0`. If this becomes
annoying, bind by device name in `retroarch.cfg` rather than index — but the four
pads will report identical names, so consider giving each a distinct Bluetooth
name via the Brook config tool if the firmware allows it. `[UNVERIFIED]`

## `mk_arcade_joystick_rpi` — not recommended

Earlier notes suggested this DKMS driver as an alternative for the GPIO buttons.
Reasons to avoid it here:

- It exists to present a *full arcade control set* (stick + buttons) on GPIO as a
  joystick device. This box has six system buttons and no stick — wrong tool.
- The commonly referenced fork is old and DKMS builds frequently fail against
  current 64-bit Pi kernels.
- It hard-codes GPIO maps that don't match the pinout in `04`.

Use the `gpio-key` overlay. Revisit only if RetroArch refuses the
keyboard+joypad split described above.
