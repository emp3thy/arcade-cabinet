# Design variant 2 — SPACE AGE: monocoque hull with TPU saddle cushion

A. CONCEPT
A monocoque hull: one continuous matte PETG top surface with the black control plate set flush inside a 1.5 mm shadow gap, plan corners R25, every edge rounded, no visible fasteners. Comfort comes from two soft printed layers: a raked TPU palm rest across the front band, and a saddle-shaped TPU lattice cushion under the flat floor that fills the valley between the thighs. Buttons and stick get thin luminous PLA rings printed into the plate so the six targets are findable in the dark. The 280 x 200 x 48/60 shell, plate, stick, buttons and cavity are unchanged.

B. GEOMETRY (changes only)
| Dimension | Old | New | Reason | Finding |
|---|---|---|---|---|
| Plan corner radius | 10 | 25 | nothing digs into thigh or palm | R2-6, R3-5 |
| Edge radii | unspecified | front R10, sides/rear R8 | sharp drop-offs dig in over hours | R2-6, R3-5 |
| Front band y0-55 | art inlay, 1 recess | 4 deep pocket (floor 44) with TPU palm rest 270 x 50 | padded angled rest, 38+ deep | R1-10, R3-5, R2-6 |
| Plate/shell joint | y55 | y50 | rest ends where fingers start | R1-10 |
| Kick row y | 80-84 | 88 / 100 / 95 (index/middle/ring) | stick level with near row | R4-6 |
| Punch row y | 120-124 | 128 / 140 / 135 | 40 row pitch kept, arc | R4-1, R4-5 |
| Second-row offset | near row +8 right | far row +8 right | Sega/Vewlix put the top row right | R4 table, R4-13 |
| Brook | x45-141, y144-192 | x175-271, y8-53 (front-right cavity) | clears raised punch nuts, mass opposite the stick | R3-4 |
| LiPo | y150-187 | y162-195 | clears punch nuts (to y158) | - |
| Antenna bracket | front wall x58 | left wall y100-130 | out from under the palm | risk H2 |
| Underside | flat + 2 strips | + TPU saddle cushion below the plane, 8-14 thick | conforming base, centring | R3-1, R3-2, R3-3, R3-4 |
| Button rings | none | luminous PLA, 3 wide, 0.5 proud | dark-room targeting, tactile | brief use case |
| Weight | ~1.5 kg est. | ~1.7 kg est. | cushion + pad | R2-3 |
| Dock | Qi pad | + 58 dia x 14 puck | reach the coil through the cushion | - |

C. PANEL
Stick stays at (75,100), 35 ball. Kick row (nearest player): index (138,88), middle (178,100), ring (218,95). Punch row: index (146,128), middle (186,140), ring (226,135). Closest pair 40.3, so 40 pitch holds; stick to kick-index 63 horizontal as before. Stick centre level with the kick middle button (R4-6). Far row sits 8 right of the near row: fingers extending from a hand rotated about 10 deg clockwise land up and to the right, which is why Sega and Vewlix offset the top row +7 (R4 table, R4-13). Each row arcs, index 12 lower than middle, ring 5 lower (R4-1, R4-5). Lowest shell height under any button 53.3 at the kick index against the 52 minimum. Palm depth: 50 soft rest plus 22 of bare plate before the kick-index rim, 72 from the front edge (R1-10 wants 38 or more). Clear panel beside the ring column to the wall: 39 (R4-7).

D. UNDERSIDE AND LAP INTERFACE
Flat floor and the two 3 mm strips stay as the datum. Below them clips a TPU 95A HF cushion, 280 x 170 (y15-185), corners R25:
- Shallow saddle cross-section: 14 thick at the outer edges tapering to 8 at x100 and x180, with a 60 wide central keel 10 thick (x110-170). Outer pads 12% gyroid; keel 6% gyroid so it squashes flat when the knees are together.
- Thigh face: 1.2 skin perforated with 6 dia holes on a 10 hex grid for grip and airflow (R2-2, R2-10, R3-8). Shell face 0.8 skin. Two grooves seat over the strips; six M3 into inserts in the floor.
- 66 dia hole at (140,38) over the coil boss; the dock carries a 58 dia x 14 puck.
Thigh spacing (R3 section 2): crests at 170 land at x55 and x225 with the keel between the thighs; at 250 near the edges; at 350 the rounded 14 edges ride the inner thigh slopes and conform. Conforming base (R3-1), centring bump (R3-2), whole width loaded (avoids R3-3). Mass: Brook front-right and LiPo right-rear opposite the steel stick, centre of mass toward the centreline and low (R3-4). About 1.7 kg total (R2-3).

E. FRONT EDGE AND WRIST
Front rim stays 48, rounded R10. Front band is a 4 deep pocket (floor 44) holding a TPU 95A pad, 6 thick at y8 rising to 9 at y50, so the surface runs 50 to 53 and slopes 4 deg down toward the player (R2-6, R3-5). At the y50 joint the pad stands 2 proud of the plate and compresses flush. Palm line at y25: 51.5, about level with the kick-row button tops (R2-11). Contact pressure a few kPa (R1-10). No forearm rest: none exists for lap sticks and support above elbow height raises shoulder load (R1-5).

F. RAKE
Keep 48/60 and 3.4 deg. Evidence favours flat or far-edge-lower on a lap (R1-4, R4-8) and lower cases (R2-4), but the wedge costs about 1.5 deg of wrist extension by Simoneau's slope (R1-4), the beanbag thigh slope of 10 deg or more dominates either way, and the wedge doubles as the rearward tilt R3-6 asks for against forward slide (R2-5). Flattening to 52/52 would spend the entire button margin. Reversing to 60/48 fails the 52 minimum at the punch row (51.2).

G. PRINT AND COST (beyond the baseline shell, plate, strips)
| Part | Material | Grams | Hours |
|---|---|---|---|
| Saddle cushion | TPU 95A HF | 160 | 11 |
| Palm rest pad | TPU 95A HF | 60 | 3 |
| Luminous rings, dual nozzle in the plate | luminous PLA + purge | 25 | +1 |
| Dock puck | PETG | 30 | 1.5 |
| Three 100 x 100 infill test tiles | TPU | 30 | 1.5 |
Total about 305 g and 18 h extra per pad. Bought: one luminous PLA spool (about 20 GBP), six extra M3 brass inserts.

H. RISKS AND FIRST TESTS
1. Cushion firmness unproven: too soft bottoms out and rocks, too firm slides. Print three tiles at 6/12/18% first and sit on them.
2. Brook and antenna near the left palm may cut wireless range. Test link quality with hands on before cutting the antenna slot.
3. Luminous rings fade after 20-30 min in the dark; 0.5 proud so they still work by touch.
4. Qi alignment through the 66 hole needs the puck to locate the pad within about 5 mm.
5. The flipped row offset contradicts the owner's template; the plate is a 4 h reprint, so test both.
With one printed shell: bare shell on beanbag and sofa, knees together and 100 apart, then with the cushion. Record rock and slide over 10 min, weigh it, photograph the wrist against the 15 deg target.

I. CONSTRAINT CHALLENGES
1. Positive rake. R1-4 and R1 thresholds say a lap surface should slope the far edge down; R4-8 says no angle for lap play. Kept because the magnitude is small and the buttons force it.
2. Height. R2-4: case height drives wrist pain more than weight. 48 front plus a cushion that compresses to about 5 gives roughly 53 effective. Forced by the reused 50 deep buttons.
3. Two edge strips. R3-3 rates two-rail bases the worst. Honoured as the datum; the cushion does the real work.
4. 280 width and 200 depth. R2-7 wants width to match thigh spread (crests up to 350); R2-8 wants depth gut to knee. Bed-limited; the cushion is the mitigation.
5. Template offset direction. The brief's near-row-right offset contradicts the Sega and Vewlix top-row-right convention (R4 table). Flipped here; the owner should check the template again.
