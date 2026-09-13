# Design variant 3, round two — OUT THERE: nested discs vs base-forward triangle

SVG plans: plan-outthere-circles.svg, plan-outthere-triangle.svg (same folder).

Coordinates: x from the left of the bounding box, y from the player's edge, mm. Both use the round-one arc (index 14 lower than middle, ring 6 lower, R4-1, R4-5), stick level with the kick middle button (R4-6), 63 horizontal to the punch column, 40 pitch, 8 offset. Fallback in both: straight rows at the same offsets. Panel face 52 above the underside under every button; flat underside; rake 0, because the beanbag lap already tips knee-down (R2-5, R3-6) and building rake into the shell would lift the palm line above 52 (R2-4).

## (a) NESTED DISCS

A Concept. One disc, 300 diameter, 52 thick, read as four concentric rings: a TPU tyre at the edge, a PETG rim band, a 250 removable PLA plate, and 2 mm raised discs on the plate (90 under the stick, 40 under each button). Under it a TPU ring is the thigh contact. It has no front and no side: the player turns it to whatever hand angle suits (R4-13) and it sits the same way at any angle.

B Plan. Circle, centre (150,150), radius 150. Bounding 300 x 300, area 70,700 mm2. Tyre crest diameter 276, plate 250. One flat facet 64 wide in the rear wall at y 296 for the port board.

C Section, heights above the underside (the compressed pad adds 4). Tyre equator 32 at r 150; tyre top 44 at r 138; rim band 46 rising to 53 at r 125 (1 mm lip); plate 52; raised discs 54. Front edge, palm line and rear are the same: 44 / 50 / 44. Panel flat.

D Panel. Stick 94,134. Kick index 165,120; middle 205,134; ring 245,128. Punch index 157,160; middle 197,174; ring 237,168. Pinky nut edge 9.5 inside the plate radius; stiffener (95 along x: 46.5-141.5, 107.5-160.5) corner 13 inside. Palm rest is the plate in front of y 100: 104 deep at the kick index, 123 to the shaft (R1-10, R4-7).

E Internals. Brook flat, x 150-246, y 200-245 (far corner 135 from centre, wall at 147.5). LiPo x 28-123, y 172-205, behind the stick body (ends y 166.5). Qi coil at 185,55, boss 62, under the right palm with no metal within 50; hole in the TPU ring. Port board rear facet x 133-163, y 293-297. Antenna bracket front wall x 116-124.

F Lap. TPU 85A ring, diameters 110-280, 6 thick, 25 percent gyroid, compresses about 2 under each crest: conforming, not two rails (R3-1, R3-3), full friction (R2-2). Chord contact per thigh 247 / 224 / 180 at crest spacing 170 / 200 / 240, so it degrades gently as the knees spread (R2-7). Steel stick 58 from centre, boards behind: mass centred and low (R3-4). Estimate 2.0 kg, the tolerated middle (R2-3). No corner meets belly, thigh or knee (R2-6, R3-5).

G Print. Shell PETG 300 x 46 tall, floor down, rim top bridged over radial ribs every 10 mm: 445 g, 20 h, single-nozzle mode (296 diameter if dual). Plate PLA 250 x 3.5 with discs: 216 g, 7 h. TPU ring 140 g, 6 h. TPU tyre printed flat as an O-ring and stretched into a rim groove: 80 g, 5 h. Total 38 h, 880 g per pad. Bought: 8 M3 inserts, 8 M3x8 screws.

H Risks and first test. Rim top spans the cavity: bridging quality. Nothing round exists in R2 or R3, and the front arc reaches 20 nearer the belly than the sides. Free rotation means it can be set crooked; the discs are the only cue. 2 kg is the upper end. Test: 300 foam disc, 52 thick, loaded to 1.8 kg, 30 min of SF2 on beanbag and sofa, knees together and 100 apart, side photo for wrist angle.

I Constraint challenges. Stiffener assumed 95 along x; if 95 along y the plate grows to 260. Arc departs from the template. Coil off the centreline: the dock needs an alignment mark. The tyre needs dual mode or a second job; drop it and the PETG roll does the job.

## (b) BASE-FORWARD TRIANGLE

A Concept. Isosceles, 320 base at the belly, 300 deep, apex clipped to a 90 flat over the knees. The wide end carries palms, stick and buttons; the tail carries the boards and nothing heavy. Three contact regions: two front corners on the thighs near the hips, the thickest and flattest part of the leg, and the tail on the knees. Apex toward the player was worked through and rejected: the taper puts the right heel 6 and the pinky button 15 from the slanted edge, the pisiform on an edge (R1-10, R2-6).

B Plan. Vertices (0,0), (320,0), (205,300), (115,300); front corners R20, tail R25. Width 320 minus 0.767y. Bounding 320 x 300, area about 60,000 mm2. Plate is the outline inset 8.

C Section. Panel 52 throughout; front edge R12 roll from 52 at y 12 to 44 at the edge; tail 52 with a 3 lip. Rake 0.

D Panel. Stick 105,90. Kick 176,76; 216,90; 256,84. Punch 168,116; 208,130; 248,124. Stiffener 57.5-152.5, 63.5-116.5, 4.4 from the plate ledge; pinky nut 5.3. Palm rest y 12-58: 46 flat plus the roll (38 minimum, R1-10), 61 to the kick index rim.

E Internals. Brook x 100-196, y 155-200. LiPo x 110-205, y 205-238. Coil 205,36, boss 62, under the right palm. Port board in the tail flat x 145-175, y 296-300. Antenna front wall x 56-64.

F Lap. TPU pad, outline inset 15, 6 thick gyroid, coil hole. Contact per thigh 142 at spacing 200 (width falls to 200 at y 142), 100 at 240. Beyond that the front corners overhang (R2-7) and with the knees apart the tail floats, leaving two short rails: R3-3. Mass forward over the hips, which slides least (R3-6). Estimate 1.8 kg.

G Print. Shell PETG 320 x 300 x 48: 355 g, 15 h, single-nozzle mode only. Plate PLA 220 g, 7 h. TPU pad 120 g, 5 h. Total 27 h, 695 g. Bought: 8 inserts, 8 screws.

H Risks and first test. 320 overhangs a small player's thighs by 45-75 a side. Tail cantilever with the LiPo. Cluster fits with 4-5 mm margins; a 2 mm error in the stiffener pocket breaks the plate edge. 300 x 280 PLA plate corners warp. Same foam test as (a), cut as a triangle.

I Constraint challenges. Fits only in single-nozzle mode: at a 310 base (dual) the cluster cannot fit at any y. Arc as (a). Three contact regions only holds with the knees together.

## J RECOMMENDATION: (a), the disc.
1 Thigh contact 224 per thigh against 142, and no width to mismatch: R3-2 and R3-3 say width mismatch is what rocks a lap board; the circle deletes the parameter.
2 Rotation gives each player the 10 degree hand angle (R4-13) without rotating the layout.
3 One rounded edge meets belly, thigh and knee alike (R2-6, R3-5).
4 Palm room 104 against 46 (R1-10, R4-7).
5 Mass centred in plan (R3-4); the triangle puts its mass on its front edge.
6 Fit margins 9.5 and 13 against 5.3 and 4.4, and it prints in either bed mode.
Costs: 11 more print hours, 185 g more plastic, about 200 g heavier, and no round lap product exists, so the foam test is the only evidence before printing.
