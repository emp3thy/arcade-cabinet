"""Lap pad, D-014: the nested disc. Stage A -- bottom shell and control plate,
no rim slope, no raised discs, no port facet, no fillets.

Geometry (mm; the API works in cm, every number below reaches Fusion as an
expression string). Disc centre is the world origin; the player sits at -Y.

SHELL (PETG). A blank cylinder shell_dia x shell_h. Three cuts:
  rebate  -- rebate_dia, rebate_h deep from the top: the plate sits here, its
             top 1 mm below the rim lip.
  core    -- core_dia straight down to the floor: the opening the plate covers,
             leaving a ledge ledge_w wide for the plate to rest on.
  under   -- cavity_dia from the floor up to under_h: hollows the shell behind
             the ledge so the wall is wall_t, the ledge ledge_t thick. The
             ledge prints as a bridged annulus (ledge_w + wall gap ~ 18 mm).
PLATE (PLA). rebate_dia less plate_clear a side, plate_t thick, sitting on
the ledge. Through-cut in one sketch: stick shaft hole, four M3 clearance
holes on the axes at stick_bolt_r, six button holes on the Sega arc. Blind
pocket stiff_w x stiff_d x stiff_t on the underside for the steel plate.

PANEL DERIVATION (matches docs/docs/06-enclosure-reference.md, D-014):
  punch column x = stick_x + stick_btn (63); punch row y = stick_y + btn_pitch
  kick column x  = punch x + row_off (8);    kick row y  = stick_y
  index button arc_idx (14) nearer the player than middle, ring arc_ring (6).
Checked against the study coordinates (150,150 origin): stick (94,134),
LK (165,120) MK (205,134) HK (245,128), LP (157,160) MP (197,174) HP (237,168).

Bolt holes are dimensioned FROM THE STICK CENTRE with horizontal/vertical
point constraints, not from the origin: two of them sit on the stick's own
axes and a zero-length origin dimension is not a dimension.
"""
FH_ATTEMPT = 2
FH_OPTS = {
    # Roots only. Every derived parameter is exercised through these.
    "only_params": [
        "shell_dia", "shell_h", "wall_t", "floor_t", "ledge_t", "ledge_w",
        "rebate_dia", "plate_t", "plate_clear",
        "stick_x", "stick_y", "stick_hole", "stick_bolt_r", "bolt_hole",
        "stiff_w", "stiff_d", "stiff_t",
        "btn_hole", "btn_pitch", "stick_btn", "row_off", "arc_idx", "arc_ring",
    ],
    "liveness_budget_s": 120,
}
INTERFERENCE_ALLOWED = []
CLEARANCES = []
# stick_bolt_r moves four holes symmetrically about the stick centre: volume,
# area, face count, bbox AND centroid stay byte-identical, so the signature
# liveness probe reads it as dead (attempt 1, measured). It is live: the
# script proves it by stepping the parameter and reading the hole axes back.
EXPECT_DEAD = ["stick_bolt_r"]
from fusionhelper.buildkit import *

import adsk.core
import adsk.fusion

MM = 0.1  # cm per mm, seeds only

PARAMS = (
    # shell
    ("shell_dia",   "276 mm", "shell outer diameter; the TPU tyre wraps outside this"),
    ("shell_h",     "53 mm",  "rim lip height"),
    ("wall_t",      "2.4 mm", "shell wall"),
    ("floor_t",     "2 mm",   "shell floor"),
    ("ledge_t",     "3.5 mm", "plate ledge thickness"),
    ("ledge_w",     "8 mm",   "plate ledge width"),
    ("rebate_dia",  "250 mm", "plate rebate diameter"),
    ("plate_t",     "3.5 mm", "plate thickness"),
    ("plate_clear", "0.35 mm", "plate radial clearance in the rebate"),
    ("rebate_h",    "plate_t + 1 mm", "derived: plate top sits 1 mm below the lip"),
    ("plate_dia",   "rebate_dia - 2 * plate_clear", "derived"),
    ("core_dia",    "rebate_dia - 2 * ledge_w", "derived: the opening inside the ledge"),
    ("cavity_dia",  "shell_dia - 2 * wall_t", "derived"),
    ("under_h",     "shell_h - rebate_h - ledge_t", "derived: cavity ceiling height"),
    ("plate_bot_z", "shell_h - rebate_h", "derived"),
    ("plate_top_z", "plate_bot_z + plate_t", "derived"),
    # panel
    ("stick_x",      "-56 mm", "stick centre x from the disc centre"),
    ("stick_y",      "-16 mm", "stick centre y from the disc centre, player at -y"),
    ("stick_hole",   "22 mm",  "shaft hole in the plate; steel plate is 21"),
    ("stick_bolt_r", "16 mm",  "M3 holes on the axes, from the stick centre"),
    ("bolt_hole",    "3.4 mm", "M3 clearance"),
    ("stiff_w",      "95 mm",  "steel stiffener, along x"),
    ("stiff_d",      "53 mm",  "steel stiffener, along y"),
    ("stiff_t",      "1 mm",   "steel stiffener pocket depth"),
    ("btn_hole",     "30.5 mm", "30 mm screw-in button hole"),
    ("btn_pitch",    "40 mm",  "button pitch, both directions"),
    ("stick_btn",    "63 mm",  "stick centre to punch column, horizontal"),
    ("row_off",      "8 mm",   "kick row sits this far right of the punch row"),
    ("arc_idx",      "14 mm",  "index button nearer the player than middle"),
    ("arc_ring",     "6 mm",   "ring button nearer the player than middle"),
    ("lp_x", "stick_x + stick_btn",            "derived"),
    ("lp_y", "stick_y + btn_pitch - arc_idx",  "derived"),
    ("mp_x", "lp_x + btn_pitch",               "derived"),
    ("mp_y", "stick_y + btn_pitch",            "derived"),
    ("hp_x", "mp_x + btn_pitch",               "derived"),
    ("hp_y", "stick_y + btn_pitch - arc_ring", "derived"),
    ("lk_x", "lp_x + row_off",                 "derived"),
    ("lk_y", "stick_y - arc_idx",              "derived"),
    ("mk_x", "lk_x + btn_pitch",               "derived"),
    ("mk_y", "stick_y",                        "derived"),
    ("hk_x", "mk_x + btn_pitch",               "derived"),
    ("hk_y", "stick_y - arc_ring",             "derived"),
)

BUTTONS = ("lp", "mp", "hp", "lk", "mk", "hk")


def ensure_params(ctx):
    for name, expr, comment in PARAMS:
        existing = ctx.up.itemByName(name)
        if existing is not None:
            if existing.expression.replace(" ", "") != expr.replace(" ", ""):
                raise RuntimeError(
                    "parameter %s already exists with expression %r, wanted %r"
                    % (name, existing.expression, expr))
            continue
        ctx.up.add(name, ctx.cbs(expr), "mm", comment)
        adsk.doEvents()


def centred_circle(ctx, sk, r_seed_cm, dia_expr, jitter):
    """Circle pinned to the sketch origin by a coincident constraint and a
    bound diameter. Jittered seed (measured: coincident-coordinate circles
    over-constrain)."""
    circles = sk.sketchCurves.sketchCircles
    c = circles.addByCenterRadius(
        ctx.pt(0.011 + 0.003 * jitter, 0.017 + 0.005 * jitter, 0), r_seed_cm)
    sk.geometricConstraints.addCoincident(c.centerSketchPoint, sk.originPoint)
    d = sk.sketchDimensions.addDiameterDimension(
        c, ctx.pt(r_seed_cm + 0.4, -0.4, 0))
    d.parameter.expression = dia_expr
    return c


def axis_circle(ctx, sk, ref_circle, dx_cm, dy_cm, r_seed_cm, dia_expr,
                dist_expr, jitter):
    """Circle on one of ref_circle's axes: horizontal-points or
    vertical-points constraint to the reference centre, one bound distance,
    bound diameter."""
    gc = sk.geometricConstraints
    rc = ref_circle.centerSketchPoint.geometry
    c = sk.sketchCurves.sketchCircles.addByCenterRadius(
        ctx.pt(rc.x + dx_cm + 0.002 * jitter, rc.y + dy_cm + 0.003 * jitter, 0),
        r_seed_cm)
    anchor = ctx.pt(rc.x + dx_cm + r_seed_cm + 0.3, rc.y + dy_cm - 0.3, 0)
    if abs(dx_cm) >= abs(dy_cm):
        gc.addHorizontalPoints(ref_circle.centerSketchPoint, c.centerSketchPoint)
        orient = ctx.dims_or.HorizontalDimensionOrientation
    else:
        gc.addVerticalPoints(ref_circle.centerSketchPoint, c.centerSketchPoint)
        orient = ctx.dims_or.VerticalDimensionOrientation
    d = sk.sketchDimensions.addDistanceDimension(
        ref_circle.centerSketchPoint, c.centerSketchPoint, orient, anchor)
    d.parameter.expression = dist_expr
    d = sk.sketchDimensions.addDiameterDimension(c, anchor)
    d.parameter.expression = dia_expr
    return c


def body_named(ctx, name):
    for b in ctx.root.bRepBodies:
        if b.name == name:
            return b
    raise RuntimeError("no body named %s" % name)


def run(_context: str):
    ctx = BuildCtx(adsk.core.Application.get())
    ensure_params(ctx)
    v = ctx.val  # cm

    # ---- datums ---------------------------------------------------------
    top_plane = ctx.plane_at_z("shell_h", "top_plane")
    floor_plane = ctx.plane_at_z("floor_t", "floor_plane")
    plate_bot_plane = ctx.plane_at_z("plate_bot_z", "plate_bot_plane")
    plate_top_plane = ctx.plane_at_z("plate_top_z", "plate_top_plane")

    # ---- shell blank ----------------------------------------------------
    sk = ctx.root.sketches.add(ctx.root.xYConstructionPlane)
    sk.name = "shell_blank"
    centred_circle(ctx, sk, v("shell_dia") / 2, "shell_dia", 1)
    if not sk.isFullyConstrained:
        raise RuntimeError("shell_blank sketch not fully constrained")
    h_cm = v("shell_h")
    f, shell = ctx.checked_newbody(
        ctx.all_profiles(sk), "shell_h",
        lambda b: (b.boundingBox.maxPoint.z > h_cm - 0.01
                   and b.boundingBox.minPoint.z > -0.01),
        "shell_blank")
    f.name = "shell_blank"
    shell.name = "shell"
    adsk.doEvents()

    # ---- rebate (from the top, down rebate_h) ---------------------------
    sk = ctx.root.sketches.add(top_plane)
    sk.name = "rebate"
    centred_circle(ctx, sk, v("rebate_dia") / 2, "rebate_dia", 2)
    f = ctx.blind_cut(ctx.all_profiles(sk), "rebate_h", [shell], "rebate")
    f.name = "rebate"
    shell = body_named(ctx, "shell")

    # ---- core (from the top, down to the floor) -------------------------
    sk = ctx.root.sketches.add(top_plane)
    sk.name = "core"
    centred_circle(ctx, sk, v("core_dia") / 2, "core_dia", 3)
    f = ctx.blind_cut(ctx.all_profiles(sk), "shell_h - floor_t", [shell], "core")
    f.name = "core"
    shell = body_named(ctx, "shell")

    # ---- undercut (from the floor, up to the ledge underside) -----------
    sk = ctx.root.sketches.add(floor_plane)
    sk.name = "undercut"
    centred_circle(ctx, sk, v("cavity_dia") / 2, "cavity_dia", 4)
    f = ctx.blind_cut(ctx.all_profiles(sk), "under_h - floor_t", [shell], "under")
    f.name = "undercut"
    shell = body_named(ctx, "shell")
    adsk.doEvents()

    # ---- plate blank ----------------------------------------------------
    sk = ctx.root.sketches.add(plate_bot_plane)
    sk.name = "plate_blank"
    centred_circle(ctx, sk, v("plate_dia") / 2, "plate_dia", 5)
    top_cm = v("plate_top_z")
    f, plate = ctx.checked_newbody(
        ctx.all_profiles(sk), "plate_t",
        lambda b: abs(b.boundingBox.maxPoint.z - top_cm) < 0.01,
        "plate_blank")
    f.name = "plate_blank"
    plate.name = "plate"
    adsk.doEvents()

    # ---- panel holes: stick, four bolts, six buttons, one sketch --------
    sk = ctx.root.sketches.add(plate_top_plane)
    sk.name = "panel_holes"
    z = top_cm
    stick = ctx.bound_circle(
        sk, (v("stick_x"), v("stick_y"), z), v("stick_hole") / 2, "stick_hole",
        x_pos="abs(stick_x)", v_pos="abs(stick_y)")
    r_bolt = v("bolt_hole") / 2
    br = v("stick_bolt_r")
    for k, (dx, dy) in enumerate(((br, 0), (-br, 0), (0, br), (0, -br))):
        axis_circle(ctx, sk, stick, dx, dy, r_bolt, "bolt_hole", "stick_bolt_r", k + 1)
    r_btn = v("btn_hole") / 2
    for name in BUTTONS:
        ctx.bound_circle(
            sk, (v(name + "_x"), v(name + "_y"), z), r_btn, "btn_hole",
            x_pos="abs(%s_x)" % name, v_pos="abs(%s_y)" % name)
        adsk.doEvents()
    if not sk.isFullyConstrained:
        loose = [i for i, c in enumerate(sk.sketchCurves.sketchCircles)
                 if not c.isFullyConstrained]
        raise RuntimeError("panel_holes loose circles: %s" % loose)
    if sk.profiles.count != 11:
        raise RuntimeError("panel_holes expected 11 profiles, got %d" % sk.profiles.count)
    f = ctx.sym_cut(ctx.all_profiles(sk), "plate_t * 3", [plate])
    f.name = "panel_holes"
    plate = body_named(ctx, "plate")
    adsk.doEvents()

    # ---- stiffener pocket on the plate underside ------------------------
    sk = ctx.root.sketches.add(plate_bot_plane)
    sk.name = "stiffener_pocket"
    ctx.bound_rect2(
        sk, (v("stick_x"), v("stick_y"), v("plate_bot_z")),
        v("stiff_w") / 2, v("stiff_d") / 2,
        u_size="stiff_w", v_size="stiff_d",
        u_pos=("stick_x", "stiff_w / 2"), v_pos=("stick_y", "stiff_d / 2"))
    if not sk.isFullyConstrained:
        raise RuntimeError("stiffener_pocket sketch not fully constrained")
    f = ctx.blind_cut(ctx.all_profiles(sk), "stiff_t", [plate], "pocket")
    f.name = "stiffener_pocket"
    plate = body_named(ctx, "plate")

    # ---- bolt-radius liveness, read back from the hole axes -------------
    def bolt_radii():
        pl = body_named(ctx, "plate")
        sx, sy = v("stick_x"), v("stick_y")
        out = []
        for face in pl.faces:
            cyl = adsk.core.Cylinder.cast(face.geometry)
            if cyl is None or abs(cyl.radius - v("bolt_hole") / 2) > 0.005:
                continue
            o = cyl.origin
            out.append(((o.x - sx) ** 2 + (o.y - sy) ** 2) ** 0.5 * 10)
        return sorted(out)

    r0 = bolt_radii()
    if len(r0) != 4 or any(abs(r - 16.0) > 0.01 for r in r0):
        raise RuntimeError("bolt holes at %s, wanted four at 16 mm" % r0)
    ctx.up.itemByName("stick_bolt_r").expression = "18 mm"
    adsk.doEvents()
    r1 = bolt_radii()
    ctx.up.itemByName("stick_bolt_r").expression = "16 mm"
    adsk.doEvents()
    r2 = bolt_radii()
    if any(abs(r - 18.0) > 0.01 for r in r1) or any(abs(r - 16.0) > 0.01 for r in r2):
        raise RuntimeError("stick_bolt_r not live: %s -> %s -> %s" % (r0, r1, r2))
    print("stick_bolt_r live: holes at %.2f -> %.2f -> %.2f mm" % (r0[0], r1[0], r2[0]))
    shell = body_named(ctx, "shell")
    plate = body_named(ctx, "plate")

    # ---- read-back ------------------------------------------------------
    for b in (shell, plate):
        bb = b.boundingBox
        print("%s: %.3f x %.3f x %.3f mm, z %.3f..%.3f, %.2f cm3, %d faces" % (
            b.name,
            (bb.maxPoint.x - bb.minPoint.x) * 10,
            (bb.maxPoint.y - bb.minPoint.y) * 10,
            (bb.maxPoint.z - bb.minPoint.z) * 10,
            bb.minPoint.z * 10, bb.maxPoint.z * 10,
            b.volume, b.faces.count))
    print("done")
