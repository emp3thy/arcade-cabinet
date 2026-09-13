# Design variant 2, round two — SPACE AGE: the Conn Station (Star Trek TNG)

SVG plan: plan-spaceage.svg (same folder).

A. Concept and source world
Star Trek: The Next Generation. Enterprise-D consoles are rounded wedges: a low apron toward the operator, a flat black LCARS panel flush in a pale shell, a raised brow behind, and a plan that fans out from the operator into a convex rear arc. That is also what the comfort research asks for: rounded chamfered front (R2-6, R3-5), nothing protruding into the thighs, wide smooth base (R3-2), low near edge (R2-4). Star Wars forms are facets, exposed structure and greebles; every facet edge is a pressure line on a thigh or palm. The object is a conn station: a fan-shaped rounded wedge with a thin undercut front lip like the knee cove of the Enterprise-D helm, a flush LCARS panel, and a rear arc rail carrying the player light bar.

B. Plan geometry
Bounding box 296 x 250, plan area about 64,800 mm2. Front edge straight, 180 long between R35 corners, 250 wide across the corners. Sides splay 8 deg outward, 250 wide at y35 to 296 at y200. Rear is a convex arc R400 (centre x148, y-150), apex y250, blended into the sides by R45 fillets. The thighs converge toward the hips, so the hip end is narrow and clears the belly while the knee end loads both thigh crests with the knees 100 apart (R3 anthropometrics; R2-7). Depth 250 fills gut-to-knee so the pad cannot rock fore-aft (R2-8). 4 mm spare on the H2D dual-nozzle bed.

C. Section geometry (z from the shell floor datum; TPU skin hangs below it)
- Front lip crown 46, lip underside 28, full round R9. Underside bow chamfer at 45 deg from (y46, z0) to (y18, z28). The undercut lip nests into the thigh-belly crease instead of being levered up by it; palms sit low and forward slide stops without a strap (R2-5, R3-6).
- Palm rest y8-58: surface 45 at y10 rising to 51 at y58, 7 deg falling toward the player (Victrix 6.3 deg, R2-6). Palm line y30: 47.5. TPU pad 3 thick inset, 1 proud.
- Plate y60-190: flat, face at 54, rake 0. Stick, kick row and punch row all at 54; every button has 54 of shell against the 52 minimum.
- Brow y195-250: rises from 54 at y195 to a 70 crest at y228, rear face drops to the datum at y250. Light bar on the player-facing slope y200-215.
- Rake 0: R1-4 and R4-8 want a lap panel flat or far-edge-low; the bow lip takes over the old wedge's rear-tilt job (R3-6).

D. Panel coordinates (x from the left of the bounding box, y from the front edge)
- Stick centre (75, 104), shaft hole 21, M3 at (59,104) (91,104) (75,88) (75,120), steel plate pocket 95 x 53 centred.
- Kick row (near): index (146, 96), middle (186, 104), ring (226, 100).
- Punch row (far): index (138, 136), middle (178, 144), ring (218, 140).
- Stick to punch index 63 horizontal; pitch 40; closest pair 40.2; far row 8 left of the near row (owner's template; on a lap the right forearm comes in from the hip so fingertips extend up-left; round one's flip is withdrawn). Arc: index 8 nearer the player than middle, ring 4 (R4-1, R4-5). Stick level with the kick middle (R4-6). Wall clearance beside the ring column 38 (R4-7), left of the stick 62 (R1-9).
- Palm rest depth: front edge to the nearest nut rim (kick index, y78) is 78; the pad is 50 deep (R1-10 asks 38+).
- LCARS tactile pills 20 x 3, 0.6 proud, between the rows at x150/190/230, accent PLA from the second nozzle.

E. Internals
- Brook 96 x 45 x 14 at x14-110, y150-195, on the floor under the plate for access, clear of the punch index nut.
- LiPo 95 x 33 x 10 at x150-245, y198-231, on the floor under the brow, opposite the steel stick to centre the mass low (R3-4).
- Qi coil 50 dia at (148, 120) on the underside, boss 62 standing 3 proud, on the keel between the thighs. Qi PCB inside at x115-145, y160-190.
- Port board 30 x 26 in the left wall at y200-230, 5 from the Brook.
- Antenna bracket in the brow at x60-80, y226-232, vertical: highest point, behind both hands, 70 from the LiPo.
- Light bar: four pill windows 28 x 5 at x88-218 on the brow slope, natural PETG fused into the black shell by the second nozzle, LEDs for player number and battery.

F. Lap interface
The underside is a hull, not a floor. A TPU 95A lattice skin, 10 nominal, covers y46-250, printed shell-face down so the thigh face carries two shallow troughs, R110, 6 deep, centrelines splaying from 160 apart at y50 to 230 at y240, with a 6 percent gyroid keel between them that flattens when the knees are together. Outer pads 12 percent gyroid, 1.2 skin perforated 6 dia on a 10 hex grid for grip and airflow (R2-2, R2-10, R3-8). Conforming (R3-1), centring (R3-2), whole width loaded (R3-3). Estimated mass 1.8 kg (R2-3).

G. Print plan
Shell 296 x 250 x 70: black PETG plus natural PETG windows, dual nozzle, floor down, 45 deg bow unsupported, 570 g plus 40 purge, 19 h.
Plate: black PLA plus accent PLA pills, dual nozzle, face down, 145 g, 4 h.
Hull skin: TPU 95A HF, shell face down, 200 g, 12 h.
Palm pad: TPU, 40 g, 2 h. Dock cradle with coil puck: PETG, 120 g, 5 h. Three TPU infill tiles: 30 g, 1.5 h.
About 1,150 g and 44 h per pad. Bought: natural PETG, TPU 95A HF, 12 M3 inserts, 4 LEDs.

H. Risks and first test
1. The 45 deg bow chamfer may curl in PETG; print the front 80 mm of the shell as a slice and sit with it to check nesting.
2. Trough splay is a guess; no data on relaxed thigh gap exists (R3 gaps). Measure the four players' crest spacing at hip and knee before slicing the skin.
3. Brook Gen 5W may not expose player LED outputs; fall back to a battery LED.
4. Bed fit is 296 of 300; if the dual-nozzle area is smaller, print single-nozzle at 325 x 320 with a snap-in diffuser.
First test: shell plus skin on beanbag and sofa, knees together and 100 apart, 10 min each; record rock and slide, weigh, photograph wrist angle against 15 deg (R1).

I. Constraint challenges
1. Panel rake 0 instead of 3.4 deg (D-013): R1-4, R4-8.
2. Front-band art inlay dropped for the TPU palm pad; identity moves to the plate pills and the brow light bar.
3. Underside TPU strips and flush coil boss dropped; hull skin and dock cradle replace them (R3-3).
4. Depth 250 and width 296 exceed 280 x 200; the addendum allows it and R2-7, R2-8 want it.
5. Antenna, port board and coil moved as in E; the coil's old spot (y38) is now under the bow undercut.
