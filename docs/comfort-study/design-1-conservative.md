# Design variant 1 — CONSERVATIVE: rounded rim, palm band, wide thigh pads

A. CONCEPT
Keep the 48/60 PETG wedge, flat underside and 280 x 200 envelope exactly as settled. Spend a small budget on the four things the research says matter most on a lap: a rounded shell rim instead of a plate-edge cliff (R2-6, R3-5), a soft palm band over 38 deep (R1-10), wide thigh pads instead of narrow rails (R3-3), and the button rows shifted 13 toward the knees with a Vewlix-style index drop so the palm heel lands on the band rather than on the edge (R4-1, R4-6). Shell, plate, three TPU pads. Nothing bought.

B. GEOMETRY CHANGES (unchanged items omitted)
| Item | Old | New | Reason, finding |
|---|---|---|---|
| Kick row centre y | 80-84 | 95; index button 85 | Heel lands on band not edge (R2-6); button-depth margin 0.8 -> 1.1; stick now within 5 of near row (R4-6) |
| Punch row centre y | 120-124 | 135; index 125 | Same shift |
| Index-column drop | 0-4 | 10, both rows | Index shorter than middle; Sega 14, Vewlix 13-14 (R4-1); six-button difference negligible so use the gentler value (R4-5) |
| Second-row offset | kick row +8 right | unchanged | See I-2 |
| Brook y | 144-192 | 148-193 | Clear punch-index rim at 141.5 |
| LiPo y | 150-187 | 156-189 | Clear punch-row rim at 151.5 |
| Top plate | 280 x 200, edge exposed | 268 x 184, flush in a 3.5 rebate; shell rim 10 wide at front, 6 at sides and rear, 45 deg underside so no support | A 3.5 plate cannot carry a radius (R2-6) |
| Front top edge | plate edge, R1.5 max | R8 on shell rim | Sharp drop-offs dig in (R2-6, R3-5) |
| Side and rear top edges | plate edge | R4 on rim | Round all edges (R2 s.3) |
| Plan corners | not stated (SCAD R10) | R15 | Same |
| Underside TPU | 2 strips ~20 wide at the edges, 3 proud | 2 pads 70 x 170 x 3, x 25-95 and 185-255, y 15-185 | Rails that miss thigh spacing rock (R3-3); friction beats weight (R2-2); channel between pads vents heat (R3-8, R2-10) |
| Front band y 0-55 | recessed art inlay | TPU palm pad 250 x 43 x 2 in a 1.5 recess, x 15-265, y 12-55, 0.5 proud | Padded front rest praised (R3-5); over 38 deep (R1-10); recess edge under the heel removed |
| Walls, floor | 2-2.5 | 2.4, 2.0 | Six 0.4 perimeters |

C. PANEL
Stick centre stays at x 75, y 100. Buttons, 40 pitch kept, no rotation:
| Button | x | y |
|---|---|---|
| Kick index (LK) | 146 | 85 |
| Kick middle (MK) | 186 | 95 |
| Kick ring (HK) | 226 | 95 |
| Punch index (LP) | 138 | 125 |
| Punch middle (MP) | 178 | 135 |
| Punch ring (HP) | 218 | 135 |
Stick-to-first-button horizontal stays 63. Closest nut gap 5.2 (index to middle, 41.2 centres). With fingers curled over the buttons the palm heel sits 50-70 in front of the near row; at y 80 that put the heel on the front edge, at y 95 it lands at y 25-45, on the pad. Palm rest depth 43 (pad) plus 10 (rim) = 53. Index drop follows finger length (R4-1); ring stays level, as Vewlix (R4-5). Shell height under the lowest button (kick index, y 85) is 53.1 against the 52 minimum. Ball 35 to nearest button rim 38.6.

D. UNDERSIDE AND LAP INTERFACE
Flat PETG floor 2.0. Two TPU pads 70 x 170 x 3 proud (95A, 40 % gyroid, give about 1 mm), printed in the same job dual-nozzle, or printed separately and glued into 1 mm keyed recesses (separate recommended for the first shell). Coil boss 62 dia, 3 proud, x 140, y 38, unchanged and flush; doubles as a small centring bump (R3-2). Pad span covers thigh crests at 170-230 with knees together and the inner slopes at wider spread (R3 s.2). Mass: stick 400-600 g at x 75; buttons ~150 g at x 180; battery ~75 g rear right; Brook ~30 g rear left; printed parts ~630 g. Total about 1.5-1.7 kg, centre of mass near x 125, y 105, z 22 (R3-4), lighter than the 2-2.5 kg tolerated middle (R2-3). No ballast.

E. FRONT EDGE AND WRIST
Front face vertical. Rim 10 wide at the top front, R8 on its outer top edge, crest at about y 7, z 48.4. At the palm line (y 30): panel 49.8, pad top 50.3. Finger pads on plungers about 3 above the panel, so heel-to-fingertip slope is about 3 deg. Sides and rear R4. No chamfer under the front face.

F. RAKE
Keep 48/60 (3.4 deg, rear high). (1) Heights locked by the 50+2 button stack under the kick row; any lower front edge needs a steeper positive rake, the direction R1-4 argues against; a level 53 slab lifts the front edge 5 (R2-4) for nothing. (2) On a beanbag the base plane is the thigh top. Hips above knees (R1 thresholds, R2-5, R3-6) plus the thigh tapering from ~180 at the hip to ~130 above the knee (R3 s.2) tilt the base roughly 8-15 deg knee-down; the pad's +3.4 deg subtracts, leaving a net far-edge-down slope of about 5-12 deg, inside R1's 7-15 deg target and ANSI's -15 to +20 (R1-3). (3) 48 at the front is at the thin end for a lever stick: Victrix 57, HRAP N 63, Panthera 64, builders 50-70 (R2 table, R2-9); only leverless boxes go under 38 (R2-4). Untested: measure the thigh slope on the actual beanbag first.

G. PRINT AND COST
Parts: shell (PETG), plate (PLA), 2 thigh pads (TPU), 1 palm pad (TPU, optional). Extra: PETG +55 g (rim and ledge), TPU +85 g, PLA -30 g. Net about +110 g, roughly GBP 4. Extra time about +5 h. Bought: nothing new; CA glue if pads print separately.

H. RISKS AND WHAT TO TEST WITH ONE SHELL
Print shell and plate, fit the owned stick and buttons, tape 250 g at the rear for electronics, play SF2 wired over USB for 30 min on the beanbag.
1. Rocking or forward slide (R3 gap). Slide: add 3M anti-slip tape (R2-2). Rock: add a 20 x 100 x 6 TPU centreline ridge at y 80-180.
2. Wrist extension: phone inclinometer on forearm and hand back, target 15 deg or under (R1-1, R1-2). Over: thicken the palm pad to 4, or level the lap with a towel (R2-5).
3. Button depth: 1.1 margin at the kick index. Measure the fitted button with connector before slicing; if short, use a 6 drop (y 89, 53.3).
4. Offset direction (I-2). A second plate costs about 8 h.
5. Ledge printing: the 45 deg underside of the 13 mm ledge; run a 40 mm coupon first.
6. Front rim pressure on pisiform and thenar over an hour (R1-10).
7. Thigh spread over 250 puts the pads on the inner slopes (R3 s.2).
8. In-place TPU on PETG may delaminate; fall back to glued pads.

I. CONSTRAINT CHALLENGES
1. Rake direction. R1-4, R1 thresholds and R4-8 say a rear-high panel is wrong on a lap. Honoured, because that evidence is desk-referenced; on a thigh the base already slopes knee-down by more than 3.4 deg (F). If the beanbag measurement shows a thigh slope under 4 deg, the wedge should flip.
2. Second-row offset. The fixed layout has the kick (near) row 8 right of the punch row. Sega and Vewlix put the far row 7 right (R4 table, R4-13). Direction depends on the elbow: elbows-in cabinet play points the forearm forward-right; on a beanbag with the elbow at the hip it points forward-left, which favours the owner's direction. Kept; test.
3. Stick midway between rows (fixed y 100) vs R4-6. The row shift gets within 5 without moving the stick.
4. Two edge strips vs R3-3. Widened into pads below the flat plane.
5. Art band. R1-10 and R3-5 want a soft rest here, and the recess edge is a line load under the heel. Art moves onto the TPU pad's top face (two-colour) or is dropped.
6. Width 280 vs R2-7 and R3 s.2 (stable only under about 250 crest spacing). Bed-limited; pads mitigate.
7. "48/60 is thick" is not supported for a lever stick (R2 table). It is thick only against leverless boxes.
