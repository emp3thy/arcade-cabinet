"""Lap pad, D-014: the nested disc. Character art on the plate, as a Fusion
DECAL (appearance only, no geometry). Run through the Fusion MCP with the
lap pad document active.

Art: cad/art/chunli.svg (owner, 2026-09-13), rasterised to cad/art/chunli.png
(2445 x 3424 px, content-cropped, transparent). Placed on the plate's top
face in the free band in front of the stick and buttons (the player's side,
-y), upright for the player:

  centre (art_cx, art_cy), art_w x art_h, on the stage G pocket floor.

Fusion decal transforms carry the decal's size in the magnitudes of the X
and Y axes (cm) -- measured 2026-09-13: the default transform for this PNG
came back as X 8.83, Y 12.37, i.e. its natural 88 x 124 mm. Set both axes
to the wanted size and the decal lands at that size.

This is a visualisation. Printing the art is a slicer job (paint the colours
from chunli.svg onto the plate's top layers, or print an inlay); the numbers
above are the placement to use there. Not a fusion-design build stage: no
parameters are bound (a decal transform cannot reference one) and no
verification stub is wanted.
"""
import adsk.core
import adsk.fusion
import math

# Size and centre now come from the stage G user parameters art_w, art_h,
# art_cx, art_cy (cad/lap_disc_g.py); the decal sits on the pocket floor at
# art_floor_z. Keep this script after stage G.
ART_PNG = r"C:\Users\gethi\source\arcade-cabinet\cad\art\chunli.png"
BUTTONS = ("lp", "mp", "hp", "lk", "mk", "hk")


def run(_context: str):
    app = adsk.core.Application.get()
    doc = app.activeDocument
    if not doc.name.startswith("Arcade Controller"):
        raise RuntimeError("wrong document " + doc.name)
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    v = lambda n: des.userParameters.itemByName(n).value
    dec = root.decals
    old = dec.itemByName("chunli")
    if old:
        old.deleteMe()
        adsk.doEvents()
    # resolve the face AFTER the delete: a held BRep handle dies on any document
    # change (R5; measured 2026-09-13 as InternalValidationError: asmFace)
    plate = [b for b in root.bRepBodies if b.name == "plate"][0]
    ART_CX_MM, ART_CY_MM = v("art_cx") * 10, v("art_cy") * 10
    ART_H_MM, ART_ASPECT = v("art_h") * 10, v("art_w") / v("art_h")
    ztop = v("art_floor_z")
    top = None
    for f in plate.faces:
        pl = adsk.core.Plane.cast(f.geometry)
        if pl is None or abs(pl.normal.z) < 0.999:  # cut floors can report a flipped surface normal
            continue
        bb = f.boundingBox
        if abs(bb.maxPoint.z - ztop) < 0.001 and bb.minPoint.x * 10 <= ART_CX_MM <= bb.maxPoint.x * 10 and bb.minPoint.y * 10 <= ART_CY_MM <= bb.maxPoint.y * 10:
            top = f
    if top is None:
        raise RuntimeError("no pocket floor face under the art centre; run stage G first")
    P, V = adsk.core.Point3D.create, adsk.core.Vector3D.create
    w = ART_H_MM * ART_ASPECT / 10.0
    h = ART_H_MM / 10.0
    centre = P(ART_CX_MM / 10, ART_CY_MM / 10, ztop)
    inp = dec.createInput(ART_PNG, [top], centre)
    inp.isChainFaces = False
    m = adsk.core.Matrix3D.create()
    m.setWithCoordinateSystem(centre, V(w, 0, 0), V(0, h, 0), V(0, 0, 1))
    inp.transform = m
    d = dec.add(inp)
    d.name = "chunli"
    o, xa, ya, _ = d.transform.getAsCoordinateSystem()
    print("decal chunli at (%.1f, %.1f) mm, %.1f x %.1f mm" % (o.x * 10, o.y * 10, xa.length * 10, ya.length * 10))
    rp = v("plate_dia") / 2
    hw, hh = xa.length / 2, ya.length / 2
    corners = [(o.x + sx * hw, o.y + sy * hh) for sx in (-1, 1) for sy in (-1, 1)]
    print("plate edge margin at corners mm:", [round((rp - math.hypot(x, y)) * 10, 1) for x, y in corners])
    discs = [("stick", v("stick_x"), v("stick_y"), v("stick_disc_d") / 2)]
    discs += [(n, v(n + "_x"), v(n + "_y"), v("btn_disc_d") / 2) for n in BUTTONS]
    for n, cx, cy, r in discs:
        dx = max(o.x - hw - cx, 0, cx - (o.x + hw))
        dy = max(o.y - hh - cy, 0, cy - (o.y + hh))
        print("  %s disc clearance %.1f mm" % (n, (math.hypot(dx, dy) - r) * 10))
    print("done")
