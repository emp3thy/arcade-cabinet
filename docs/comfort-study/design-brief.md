# Lap arcade pad — current design, for ergonomic review (2026-09-12)

Units mm. Coordinates: x left-right from the pad's left edge, y front-to-back from the front edge (the edge nearest the player).

## Use case
- Wireless arcade controller, one per player, up to four players, resting on the player's lap.
- Seating: beanbags and sofas in a dark room, projector on the wall. Low, soft, no table, no armrest.
- Sessions 1-3 hours, mostly Street Fighter II and similar 6-button fighters, plus other arcade games.
- Players: adults, mixed. Pad must be identical for all four.
- Play on the internal battery; recharge afterwards on a Qi dock. No cables during play.

## Fixed constraints (settled, do not change; flag if the research says they are wrong)
- Envelope 280 wide x 200 deep. Chosen so the shell prints in one piece on a Bambu H2D in dual-nozzle mode (300 x 320 bed).
- Profile: wedge, 48 tall at the front edge, 60 at the rear edge, 3.4 degree panel rake toward the player, flat underside. (D-013.) Heights are forced by the reused cabinet buttons: 50 below the panel face with connector and wire, plus a 2 floor.
- Top plate 3.5 thick PLA, removable; bottom shell PETG.
- Joystick and six 30 mm buttons are reused from an old cabinet (D-009). Stick: shaft hole 21, mounting holes on the axes 16 from centre, 4x M3x12 into a 53 x 95 x 1 steel stiffener plate pocketed into the plate underside, body 34 deep below the steel, footprint 75 x 65. Buttons: screw-in, nut about 36 diameter, 40 body depth, ~50 with connector.
- Panel layout (confirmed against the owner's old joystick template): stick centre x 75, y 100. Buttons on 40 pitch both directions, second row offset 8. Punch row centres x 138 / 178 / 218 at y 120-124; kick row x 146 / 186 / 226 at y 80-84. Stick centre to nearest button centre 63.
- Internals: Brook Gen 5W board 96 x 45 x 14 at x 45-141, y 144-192; LiPo 95 x 33 x 10 at x 168-267, y 150-187; Qi receiver coil (50 diameter) on the underside centreline at x 140, y 38, in a boss 62 diameter standing 3 proud; port board in the left wall at y 148-178; antenna bracket on the front wall at x 58.
- Underside: flat, with two TPU strips 3 proud running front-to-back along both long edges (the thigh contact lines). Coil boss flush with the strips.
- Front band y 0-55 carries a recessed art inlay (about 260 x 55). No controls there.
- Materials: PETG shell, PLA plate, TPU strips, printed on Bambu H2D. The owner can print anything that fits the bed.
- Two-part shell, top plate removable, snap tabs plus M3 into brass inserts.

## Things that are NOT fixed and can be changed
- Anything about the underside shape below the flat plane (add-on pads, cushions, contours), as long as the internal cavity keeps its depth.
- Edge radii, front-edge shape, palm rest treatment, any wrist rest or forearm support added in front of or beside the controls.
- Where on the 280 x 200 the control cluster sits, within the envelope and clear of the internals (the internals can move too).
- Whether the front band is art or something else.
- Ball top size, stick spring/tension, actuator, restrictor gate — but the stick body itself is fixed.
- Rake angle, within the 48/60 heights (a different rake changes the heights; say so if you propose it).
- Weight: not measured yet. Estimate from the shell volume: roughly 280 x 200 x 54 outer, 2-2.5 walls, plus about 250 g of electronics and battery, plus buttons and stick (the stick alone is a steel-bodied cabinet part, several hundred grams).
- Strap, thigh cut-outs, lap cushion, anything worn or placed on the lap.

## Known concerns already raised
- 48/60 is thick for a lap stick. The original 26/46 saddle wedge with a concave belly was abandoned because the reused parts did not fit under it.
- A flat slab on two thighs bridges the gap between them and may rock or slide forward on a beanbag.
- Front edge height (48) puts the wrists high relative to the thighs.
- Weight is unknown and may be high because of the steel stick.

## Required outcomes (owner, 2026-09-12)
The review must produce THREE distinct design variants, each meeting the fixed constraints above and each justified against the research:
1. **Conservative** — comfortable, cost-conscious, simple shape. Easy to print, few parts, no exotic materials. The version to build first.
2. **Space age** — comfort first, with a clean futuristic look. More parts and print time are acceptable if they earn their place.
3. **Out there** — comfort first, unconventional. Allowed to challenge assumptions about what a lap controller is (straps, cushions, split units, articulation, body-worn elements), as long as the fixed constraints hold or the violation is flagged explicitly.
For each variant give: the geometry (numbers), what changes from the current design, which research findings drive each change, estimated extra print time and material, and the risks.
