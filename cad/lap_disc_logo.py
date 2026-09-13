"""Lap pad, D-014: the nested disc. Street Fighter II logo on the plate, as a
Fusion DECAL (appearance only, no geometry). Run through the Fusion MCP with
the lap pad document active.

Art: C:\\dev\\sf2_svg (owner, 2026-09-13). Two colour layers, one per DXF
layer: C00_ED1C24 red #ed1c24 (16 closed polylines) and C01_120203 near
black #120203 (51 closed polylines); together 199.83 x 102.10 mm at the
owner's scale, aspect 1.9569. Rasterised from _combined.svg to
cad/art/sf2_logo.png (2998 x 1532 px, content-cropped, transparent).

Placed on the plate's top face in the free band above the buttons (+y):

  centre (LOGO_CX, LOGO_CY), LOGO_W wide, height from the PNG's aspect.

The band is bounded below by the top button's raised disc, which reaches
y 41, and above by the plate rim at r 124.65. LOGO_W 117 leaves 2 mm to the
disc and 6.4 mm from the top corners to the rim. That is the practical
ceiling: the round plate cuts the corners away faster than the extra width
buys, so even at a 4 mm rim margin the logo only reaches about 120 mm.

Fusion decal transforms carry the decal's size in the magnitudes of the X
and Y axes (cm), so both axes are set to the wanted size.

This is a visualisation. Printing the logo is a slicer job: paint the two
colours from cad/art/logo/*.svg onto the plate's top layers. Not a
fusion-design build stage -- no parameters are bound (a decal transform
cannot reference one) and no verification stub is wanted.
"""
import adsk.core
import adsk.fusion
import math

LOGO_PNG = r"C:\Users\gethi\source\arcade-cabinet\cad\art\sf2_logo.png"
LOGO_ASPECT = 2998.0 / 1532.0   # the cropped PNG
LOGO_W = 117.0                  # mm, the practical maximum (see below)
LOGO_CX = 0.0                   # mm
LOGO_BOTTOM = 43.0              # mm, 2 clear of the top button disc at y 41
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
    old = dec.itemByName("sf2_logo")
    if old:
        old.deleteMe()
        adsk.doEvents()
    # resolve the face AFTER the delete: a held BRep handle dies on any document
    # change (R5; measured 2026-09-13 as InternalValidationError: asmFace)
    plate = [b for b in root.bRepBodies if b.name == "plate"][0]
    h_mm = LOGO_W / LOGO_ASPECT
    cy_mm = LOGO_BOTTOM + h_mm / 2.0
    ztop = v("plate_top_z")
    top = None
    for f in plate.faces:
        pl = adsk.core.Plane.cast(f.geometry)
        if pl is None or abs(pl.normal.z) < 0.999:
            continue
        bb = f.boundingBox
        if abs(bb.maxPoint.z - ztop) < 0.001 and abs(bb.minPoint.z - ztop) < 0.001:
            if top is None or f.area > top.area:
                top = f
    if top is None:
        raise RuntimeError("no plate top face at z %.1f" % (ztop * 10))
    P, V = adsk.core.Point3D.create, adsk.core.Vector3D.create
    centre = P(LOGO_CX / 10.0, cy_mm / 10.0, ztop)
    inp = dec.createInput(LOGO_PNG, [top], centre)
    inp.isChainFaces = False
    m = adsk.core.Matrix3D.create()
    m.setWithCoordinateSystem(centre, V(LOGO_W / 10.0, 0, 0), V(0, h_mm / 10.0, 0), V(0, 0, 1))
    inp.transform = m
    d = dec.add(inp)
    d.name = "sf2_logo"
    o, xa, ya, _ = d.transform.getAsCoordinateSystem()
    print("decal sf2_logo at (%.1f, %.1f) mm, %.1f x %.1f mm" % (
        o.x * 10, o.y * 10, xa.length * 10, ya.length * 10))
    rp = v("plate_dia") / 2
    hw, hh = xa.length / 2, ya.length / 2
    corners = [(o.x + sx * hw, o.y + sy * hh) for sx in (-1, 1) for sy in (-1, 1)]
    print("plate edge margin at corners mm:",
          [round((rp - math.hypot(x, y)) * 10, 1) for x, y in corners])
    discs = [("stick", v("stick_x"), v("stick_y"), v("stick_disc_d") / 2)]
    discs += [(n, v(n + "_x"), v(n + "_y"), v("btn_disc_d") / 2) for n in BUTTONS]
    for n, cx, cy, r in discs:
        dx = max(o.x - hw - cx, 0, cx - (o.x + hw))
        dy = max(o.y - hh - cy, 0, cy - (o.y + hh))
        print("  %s disc clearance %.1f mm" % (n, (math.hypot(dx, dy) - r) * 10))
    print("done")
