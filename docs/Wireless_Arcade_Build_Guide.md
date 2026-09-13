> **SUPERSEDED — 2026-09-06.** This guide is kept for history. Authoritative
> documentation now lives in `CLAUDE.md` and `docs/`. Known errors in this file:
> the `gpio-keys` overlay name (should be `gpio-key`), the +3.3V button wiring
> (should be GPIO→GND), and the 2–3 hour charge-time claim. See
> `docs/08-open-issues.md`.

# Wireless Arcade Cabinet Build Guide

## Project Overview

This build guide documents a modular wireless lap-mounted arcade controller project paired with a Raspberry Pi 4 running RetroPie. The system features:

- **Modular wireless lap-mounted arcade controllers** with multiple independent units
- **Qi wireless charging** for cable-free charging between play sessions
- **Brook Gen 5W wireless fighting board** as the encoder, communicating via Bluetooth to the Pi
- **Raspberry Pi 4 running RetroPie** as the central console
- **Local console buttons** for multi-player game control and system navigation

This setup provides a clean, wireless gaming experience without cable tethering, while maintaining low latency through dedicated arcade-grade hardware.

---

## Corrected Bill of Materials

### Lap Pad (per controller)

| Item | Part | Status |
|------|------|--------|
| Wireless Encoder | Brook Gen 5W Wireless Fighting Board | PURCHASED |
| Battery Charger | TP4056 charging module (with DW01 protection) | PURCHASED |
| Battery | 3.7V 3700mAh 103395 LiPo battery pack | PURCHASED |
| Wireless Charging | Qi wireless charging receiver module (5V output) | PURCHASED |
| Display | Small OLED screen for Brook Gen 5W | PURCHASED |
| Input - Stick | 8-way joystick (from existing cabinet) | HAVE |
| Input - Buttons | 6x 30mm arcade push buttons (from existing cabinet) | HAVE |
| Connectors | JST PH 2.0mm pigtails/connectors (for Brook board battery connection) | NEEDED |
| Wiring | Wires, crimp connectors, quick-disconnect harness connectors | HAVE |
| Enclosure | 3D printed enclosure | NEEDED |
| Charging Pad | Qi wireless charging transmitter pad (one per charging station) | PURCHASED |

**Important Note:** The MT3608 boost converter is **NOT needed** for this build. The Brook Gen 5W operates natively at 3.7V from the LiPo battery, eliminating the need for voltage boost circuitry and simplifying the power chain.

### Pi Console Box

| Item | Part | Status |
|------|------|--------|
| Console | Raspberry Pi 4 Model B | HAVE |
| Input - Buttons | 6-8 arcade push buttons (Start, Select, Hotkey, Player 1-4) | HAVE |
| Wiring | Wires, Dupont connectors | HAVE |
| Access | USB-C panel mount (optional, for clean access to Pi) | NEEDED |
| Enclosure | Enclosure | NEEDED |

**Important Note:** 10kΩ pull-down resistors are **optional** — the Pi 4 has configurable internal pull-ups/pull-downs via the gpio-keys overlay. External resistors provide additional stability but are not strictly necessary.

---

## Lap Pad Wiring Instructions

### Simplified Power Chain (NO boost converter)

The power distribution architecture is designed for maximum simplicity:

```
[Qi Receiver 5V out] → [TP4056 IN+ / IN-] → charges → [3700mAh LiPo]
[LiPo 3.7V] → [JST PH 2.0mm connector] → [Brook Gen 5W BAT connector]
[Joystick + 6 Buttons] → [Brook Gen 5W input terminals]
[OLED display] → [Brook Gen 5W I2C/display header]
```

This chain removes the boost converter entirely, as the Brook Gen 5W is explicitly rated for 3.7V operation from LiPo cells.

### Step-by-Step Wiring

#### 1. Qi Receiver to TP4056 Charger

Solder the Qi receiver output to the TP4056 charging module:

- **Qi Receiver V+ (output)** → **TP4056 IN+**
- **Qi Receiver GND** → **TP4056 IN-**

The Qi receiver module outputs regulated 5V DC, which is exactly what the TP4056 charging module expects on its input. This 5V safely charges the TP4056's internal circuitry without damage.

#### 2. TP4056 to LiPo Battery

Connect the charging module to the battery:

- **TP4056 BAT+** → **LiPo positive terminal**
- **TP4056 BAT-** → **LiPo negative terminal**

The TP4056 includes a built-in DW01 protection IC that handles:
- Overcharge protection (stops charging at ~4.2V)
- Over-discharge protection (disconnects at ~2.5V)
- Short circuit protection

This provides comprehensive battery safety without additional components.

#### 3. Battery to Brook Gen 5W

The Brook Gen 5W has a dedicated JST PH 2.0mm battery connector. Prepare the LiPo leads:

- Re-terminate the LiPo leads with a JST PH 2.0mm plug, or
- Use a JST PH 2.0mm pigtail adapter and crimp connectors

Connect to the Brook board:
- **Battery positive** → **Brook Gen 5W BAT+ (red wire)**
- **Battery negative** → **Brook Gen 5W BAT- (black wire)**

**CRITICAL:** Verify polarity before powering on. Reversed polarity will permanently destroy the Brook Gen 5W board. Double-check with a multimeter if unsure.

#### 4. Joystick Wiring

The joystick provides four directional inputs (UP, DOWN, LEFT, RIGHT):

- **Joystick UP** → **Brook Gen 5W UP terminal**
- **Joystick DOWN** → **Brook Gen 5W DOWN terminal**
- **Joystick LEFT** → **Brook Gen 5W LEFT terminal**
- **Joystick RIGHT** → **Brook Gen 5W RIGHT terminal**
- **Joystick Common/GND** → **Brook Gen 5W GND terminal**

The joystick common wire (typically the black or green wire) connects to ground on the Brook board. The Brook board provides the switch logic for directional inputs.

#### 5. Button Wiring

Connect the 6 action buttons to the Brook Gen 5W's button input terminals:

- **Button 1** → **Brook Gen 5W P1 terminal**
- **Button 2** → **Brook Gen 5W P2 terminal**
- **Button 3** → **Brook Gen 5W P3 terminal**
- **Button 4** → **Brook Gen 5W P4 terminal**
- **Button 5** → **Brook Gen 5W P5 terminal**
- **Button 6** → **Brook Gen 5W P6 terminal**
- **All button grounds** → **Brook Gen 5W GND terminal**

Each button should have one terminal connected to the corresponding input and the other terminal to GND.

#### 6. OLED Display Wiring

Connect the OLED display to the Brook Gen 5W's display header:

- **OLED SDA** → **Brook Gen 5W I2C SDA pin**
- **OLED SCL** → **Brook Gen 5W I2C SCL pin**
- **OLED VCC** → **Brook Gen 5W 3.3V or 5V pin** (check module requirements)
- **OLED GND** → **Brook Gen 5W GND**

Verify your specific OLED module's I2C address for compatibility with the Brook board's display driver.

### Charging Conflict Warning

**Critical Issue:** The Brook Gen 5W has its own USB-C charging circuit built into the board. If you connect USB-C power to the Brook board while the controller is simultaneously sitting on a Qi wireless charging pad, two independent chargers will compete to charge the same LiPo cell. This can cause:

- Charging circuit damage
- Battery stress and reduced lifespan
- Potential thermal runaway

**Solution:**

- **Use Qi wireless charging exclusively** for routine charging via the TP4056
- **Use USB-C on the Brook board only for:**
  - Wired gameplay when away from wireless charging
  - Firmware updates and configuration
  - **NOT for charging the battery**

If you need to update firmware while charging, use only the Qi pad and do not plug in USB-C simultaneously.

---

## Pi Console Box Wiring

### GPIO Pin Assignments

The following GPIO pins on the Raspberry Pi 4 are assigned to console control buttons. These buttons are used for player start inputs, select, and hotkey functions in multi-player and cabinet scenarios.

| Button | GPIO (BCM) | Physical Pin | Purpose |
|--------|-----------|-------------|---------|
| Player 1 Start | GPIO17 | Pin 11 | Player 1 game start input |
| Player 2 Start | GPIO27 | Pin 13 | Player 2 game start input |
| Player 3 Start | GPIO22 | Pin 15 | Player 3 game start input |
| Player 4 Start | GPIO23 | Pin 16 | Player 4 game start input |
| Select | GPIO24 | Pin 18 | Menu select / game select |
| Hotkey | GPIO25 | Pin 22 | RetroPie hotkey (exit game, menus) |
| Ground | GND | Pin 6, 9, or 14 | Common ground for all buttons |

### Button Wiring Schematic

Each button connects between +3.3V and a GPIO pin:

```
+3.3V ─── [Button] ─── GPIO Pin
                           │
                      [10kΩ resistor] (optional with internal pull-downs)
                           │
                          GND
```

**Pin 1** provides +3.3V (verified from official Pi pinout documentation).

**Connection Method:**

1. Solder +3.3V from Pin 1 to one terminal of each button
2. Solder the other button terminal to its corresponding GPIO pin
3. Add a 10kΩ pull-down resistor between each GPIO pin and GND (optional if using internal pull-downs via software configuration)
4. Connect a common ground wire from Pin 6, 9, or 14 to your ground rail

The internal pull-down configuration in the gpio-keys overlay eliminates the need for physical pull-down resistors, but adding them provides electrical stability and noise filtering.

---

## RetroPie Configuration

### CORRECTED gpio-keys Overlay Config

The original configuration used incorrect key codes. Below is the **corrected configuration** with proper Linux input event codes for arcade and gamepad use.

Add these lines to `/boot/config.txt`:

```
# CORRECTED key codes for RetroPie gamepad emulation
# Using BTN_* codes for proper gamepad recognition

dtoverlay=gpio-keys,gpio=17,keycode=2,label="Player 1 Start"
dtoverlay=gpio-keys,gpio=27,keycode=3,label="Player 2 Start"
dtoverlay=gpio-keys,gpio=22,keycode=4,label="Player 3 Start"
dtoverlay=gpio-keys,gpio=23,keycode=5,label="Player 4 Start"
dtoverlay=gpio-keys,gpio=24,keycode=6,label="Select"
dtoverlay=gpio-keys,gpio=25,keycode=7,label="Hotkey"
```

#### Why KEY_1 through KEY_6 instead of BTN_START?

The gpio-keys overlay creates a single virtual input device. If all 4 player Start buttons used the same keycode (BTN_START = 315), the system couldn't distinguish which player pressed Start. Instead, we map each button to a unique keyboard key (KEY_1=2 through KEY_6=7), then map those keys in RetroArch's input config to the appropriate player actions.

#### Linux Input Event Code Reference

| Button Name | Code | Use Case |
|------------|------|----------|
| KEY_1 | 2 | Player 1 Start (mapped in RetroArch) |
| KEY_2 | 3 | Player 2 Start |
| KEY_3 | 4 | Player 3 Start |
| KEY_4 | 5 | Player 4 Start |
| KEY_5 | 6 | Select |
| KEY_6 | 7 | Hotkey |
| BTN_SOUTH | 304 | A / Cross button (for Brook controllers) |
| BTN_EAST | 305 | B / Circle button |
| BTN_NORTH | 307 | X / Triangle button |
| BTN_WEST | 308 | Y / Square button |

#### Important Limitation of gpio-keys

**Critical Note:** The `gpio-keys` overlay creates a **virtual keyboard device**, not a gamepad. While this approach works, it requires additional RetroArch keyboard-to-gamepad mapping and may not be natively recognized by EmulationStation as a proper game controller.

For better RetroPie integration, consider using the `mk_arcade_joystick_rpi` driver (see below), which presents GPIO buttons as proper joystick devices that EmulationStation recognizes natively.

### Alternative: mk_arcade_joystick_rpi Driver

For a more robust and RetroPie-friendly solution, install the `mk_arcade_joystick_rpi` driver. This driver presents GPIO buttons as proper joystick devices (`/dev/input/jsX`), which EmulationStation recognizes without additional keyboard mapping.

#### Installation

```bash
cd /home/pi
git clone https://github.com/recalbox/mk_arcade_joystick_rpi.git
cd mk_arcade_joystick_rpi
sudo mkdir /usr/src/mk_arcade_joystick_rpi-0.1.5
sudo cp -a * /usr/src/mk_arcade_joystick_rpi-0.1.5/
sudo dkms build -m mk_arcade_joystick_rpi -v 0.1.5
sudo dkms install -m mk_arcade_joystick_rpi -v 0.1.5
```

#### Loading the Driver

After installation, load the driver with:

```bash
sudo modprobe mk_arcade_joystick_rpi map=1
```

To load automatically on boot, add the following to `/etc/modules`:

```
mk_arcade_joystick_rpi
```

The `map=1` parameter specifies the GPIO-to-button mapping configuration. Consult the driver documentation for detailed mapping options.

### Brook Gen 5W Pairing with RetroPie

The Brook Gen 5W communicates with the Raspberry Pi via Bluetooth. Follow these steps to pair and configure:

1. **Enter Pairing Mode on Brook Board:**
   - Locate the pairing button on the Brook Gen 5W (usually a small button on the board)
   - Hold the pairing button for 3 seconds
   - The LED on the board should flash rapidly, indicating pairing mode is active

2. **Pair via RetroPie UI:**
   - On the Raspberry Pi, access the RetroPie Setup menu
   - Navigate to: **RetroPie Setup > Configuration / Tools > Bluetooth**
   - Select **"Register and Connect to Bluetooth Device"**
   - Wait for the system to scan for nearby Bluetooth devices
   - The Brook Gen 5W should appear in the list
   - Select it and confirm the pairing

3. **Verify Pairing:**
   - The LED on the Brook board should stop flashing and remain steady or pulse slowly
   - Check in RetroPie that the device is listed as "Connected"

4. **Configure in EmulationStation:**
   - Once paired, exit to the EmulationStation main menu
   - Press the **Start button** to open the menu
   - Navigate to **Controller Settings > Configure Input**
   - Select the Brook controller and map its buttons to EmulationStation's expected inputs
   - Save the configuration

### RetroArch Configuration for Multiple Players

If you have multiple Brook controllers or wireless pads, configure RetroArch to map each device to a player slot.

Edit `/opt/retropie/configs/all/retroarch.cfg` and add:

```
input_player1_joypad_index = "0"
input_player2_joypad_index = "1"
input_player3_joypad_index = "2"
input_player4_joypad_index = "3"
```

Where the index numbers correspond to the order in which the joystick devices appear in `/dev/input/` (typically assigned in the order they are connected or powered on).

You can verify joystick indices by running:

```bash
ls -la /dev/input/js*
```

Each Brook controller paired should appear as a separate `jsX` device.

---

## Testing Checklist

Before considering your build complete, verify all components and functionality:

### Power and Charging

- [ ] Qi receiver charges battery through TP4056 (check TP4056 status LED: red = charging, blue/green = fully charged)
- [ ] Battery voltage reads approximately 3.7V nominal when measured with a multimeter
- [ ] Battery holds voltage for at least 5 minutes after charging

### Brook Gen 5W Controller

- [ ] Brook Gen 5W powers on from battery (LED indicator lights up or pulses)
- [ ] All 4 joystick directions (UP, DOWN, LEFT, RIGHT) register consistently
- [ ] All 6 action buttons register when pressed
- [ ] OLED display (if installed) shows status information and responds to button presses
- [ ] Bluetooth pairing successful with Pi (LED pattern changes after pairing)
- [ ] Wireless range is adequate (minimum 10 feet recommended)

### Pi Console Box

- [ ] All Pi console buttons (Player 1-4 Start, Select, Hotkey) register in GPIO testing
- [ ] GPIO testing confirms proper voltage and signal transmission
- [ ] Pi boots successfully with new gpio-keys overlay or mk_arcade_joystick_rpi driver

### EmulationStation Integration

- [ ] Brook controller appears as an input device in EmulationStation controller configuration
- [ ] All Brook buttons and joystick inputs are correctly mapped in EmulationStation
- [ ] Console buttons work in EmulationStation menus and game selection
- [ ] Controller configuration is saved and persists after reboot

### Wireless Charging

- [ ] Controller charges on Qi pad when placed down
- [ ] Charging indicator on TP4056 shows red (charging) when pad is active
- [ ] Full charge achieved within 2-3 hours
- [ ] Controller operates normally after wireless charge

### Safety and Conflict Testing

- [ ] No charging conflict when attempting USB-C connection during Qi charging (test carefully - monitor for heat, unusual LED behavior, or board damage)
- [ ] If USB-C is plugged in during Qi charging, unplug one immediately to prevent dual-charger damage
- [ ] Battery does not overheat during extended play or charging
- [ ] No visible damage to wiring, solder joints, or connectors

### Game Functionality

- [ ] Start a game and confirm all controller inputs work in-game
- [ ] Test joystick sensitivity and button response in game menu and during gameplay
- [ ] Verify that hotkey functions work (exit game, menu access, etc.)
- [ ] Test multiple controllers simultaneously in a multi-player game
- [ ] Verify Bluetooth connection remains stable during extended play (no dropouts or lag)

