# Design variant 3 — OUT THERE: the Harness Saddle

A. Concept
The pad is worn, not balanced. Three add-ons turn the unchanged 48/60 shell into a harnessed saddle. (1) A loose microbead saddle bag under the shell fills the valley between thighs and beanbag and tilts the panel knee-end-down (R3-1, R3-6). (2) A full-width forearm shelf clipped to the belly-side edge lets the forearms rest at panel height so the wrists run straight (R1-4, R1-5, R1-9, R1-10). (3) A hip belt from the shelf ends round the lower back stops the pad creeping down the sloping lap and makes it follow the player when they shift (R2-2, R2-5). Rejected: split left/right units (stick-to-button relation must stay fixed, R4-4, R4-6); hip-bridging cushions (R3-7) sink into a beanbag.

B. Geometry changes (mm, brief coordinates)
| Item | Old | New | Reason | Finding |
|---|---|---|---|---|
| Kick row centres | x 146/186/226, y 80-84 | (146,86) (186,100) (226,94) | stick level with bottom row; Sega arc, index 14 lower, ring 6 lower than middle | R4-6, R4-1 |
| Punch row centres | x 138/178/218, y 120-124 | (138,126) (178,140) (218,134) | same arc, 40 row pitch and 8 offset kept | R4-1, R4-2 |
| Control-free front band | y 0-55 | y 0-68 | palm room ahead of cluster | R4-7, R1-10 |
| Brook board | x 45-141, y 144-192 | x 20-116, y 144-192 | clear punch-index nut (x 120-156, y 108-144) | brief |
| LiPo | x 168-267, y 150-187 | x 180-275, y 162-195 | clear punch-middle nut (y 122-158) | brief |
| Shell height at lowest button centre | 52.8 at y 80 | 53.2 at y 86 | 48/60 wedge unchanged | brief |
| Net panel angle | +3.4 (knee end higher) | -5 on a level seat, about -15 on a sloping lap | bag wedge 25 front / 55 rear | R1-4, R3-6 |
| Forearm shelf (new) | none | 280 x 60 at y -60 to 0, top 46 at the join, 42 at the nose, nose R12 | palm support over 38 deep, sloped front | R1-10, R3-5, R2-6 |
| Saddle bag (new) | two TPU rails only | 280 x 220 bag, y -20 to 200, 25 thick front, 55 rear, 60 percent fill | conforming base, no rails | R3-1, R3-3 |
| Keel (new) | flat floor | TPU ridge 30 wide, y 75-195, 15 tall, on centreline | centring bump | R3-2 |
| Hip belt (new) | none | 38 webbing, anchors at shelf ends x 0-15 and 265-280 | stop forward creep on slope | R2-2, R2-5, R3-6 |

C. Panel
Stick stays at (75,100). Cluster moves up 16 and arcs so the stick is level with the kick-row middle button (R4-6). Punch row 40 above kick row with the 8 offset; neighbour spacings 40.4 to 42.4. Index column 14 nearer the player than middle, ring 6 nearer (Sega P1 arc, R4-1, R4-5). No 10 deg rotation. Stick-to-punch-column 63 kept. Palm depth 71 from front edge to nearest button rim, plus the 60 shelf. Fallback: straight rows and only the +16 shift.

D. Lap and body interface
- Saddle bag: cotton or mesh zipped cover 280 x 220, 60 to 80 g of 1-3 mm EPS microbeads at about 60 percent fill. 25 thick under the belly edge, 55 under the knee edge, 8.5 deg knee-down tilt. 100 x 100 hook-and-loop patch mates with the shell floor between the TPU rails, clear of the coil boss; pad lifts off for the Qi dock. Beads fill any crest spacing 170 to 350 (R3-1).
- Keel: TPU 95A ridge on the centreline pushes beads outward so the pad self-centres (R3-2). Starts at y 75 to clear the coil boss.
- Belt: 1.5 m of 38 mm polypropylene webbing, side-release buckle, ladder lock, printed loops on the shelf ends. Tension only enough to hold position.
- Mass: steel stick at x 75 dominates; bag spreads it; centre of mass about 30 above the thigh line (R3-4).

E. Front edge and wrist
Shelf top 2 below the panel plane at the join, falls 4 over its 60 depth toward the body; nose R12; 10 mm TPU 85A gyroid pad on a ribbed PETG shelf bolted to two M3 inserts in the front wall at x 20 and 260, clear of the antenna bracket at x 58. Palm line 46 above shell base, about 71 above the thigh on the bag, forearm supported at the same height (R1-5, R2-11). Other top edges R8.

F. Rake
Shell 48/60 unchanged. Corrective rake from the bag, adjustable by fill and belt tension: net -5 deg on a level sofa, about -15 on a sloping beanbag lap. R1-4: 9 deg extension at -15 slope vs 22 at +15. 52 rule holds: 53.2 at the new lowest button centre, 52.1 at that button's nut edge (y 68).

G. Print and cost, per pad
| Part | Material | g | h |
|---|---|---|---|
| Forearm shelf with belt loops | PETG | 110 | 5 |
| Shelf pad, gyroid 15 percent | TPU 85A | 60 | 4 |
| Keel | TPU 95A | 25 | 1.5 |
About 195 g and 10.5 h per pad, 42 h for four. Bought: microbeads 1 kg £8 (all four), cushion cover £3, hook-and-loop £1, webbing £2, buckle and ladder lock £2, two M3 inserts £0.50. About £45 for four.

H. Risks and cheap tests first
- Belt may feel restrictive; no product exists.
- Bag heat and sweat (R2-10, R3-8). Mesh cover; fallback printed TPU gyroid cushion.
- 71 palm line may sit above the elbow for a reclined player (R1-5). Measure elbow-to-thigh height for all four players in the beanbags.
- Arc departs from the owner's template; muscle memory risk.
- Board and battery move; port board has 17 to the Brook; battery 2.5 from rear wall.
- Cantilevered shelf may crack at the bolts; 3 walls and ribs.
- Qi charging needs the pad lifted off the bag every time.
Test before any shell print, under £10: foam block 280 x 200 x 54 with 1.7 kg inside, pillowcase with 70 g of beads, luggage strap round the lower back, rolled towel as the shelf. Thirty minutes of SF2 on beanbag and sofa, knees together and 100 apart. Side photo for wrist angle.

I. Constraint challenges
- The two TPU underside rails are exactly the two-rail base R3-3 criticises. Kept because fixed, buried under the bag; delete if the bag proves out.
- Panel layout arc and +16 shift proposed under the grant on offset and arc. Fallback: template as is.
- 48/60 with 3.4 deg positive rake is the wrong direction for a lap (R1-4). Reversing the wedge fails the 52 rule at the raised punch row (51.6 at y 140), so correction is done outside the shell.
- "Identical for all four" kept for printed parts; belt length and bag fill are per-player.
- No research covers straps, beads under a fightstick, or beanbag seating; foam mock-up is the only evidence that matters.
