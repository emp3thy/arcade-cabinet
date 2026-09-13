"""Lap pad, D-014: the nested disc. Stage B -- runs in the document that holds
stage A (cad/lap_disc.py) and adds, in order:

  rim slope    a distance-and-angle chamfer on the shell's outer top edge:
               rim_slope_w across the top, rim_slope_h down the wall, so the
               rim band falls from shell_h at the lip to shell_h - rim_slope_h
               at the outside. A flat lip rim_lip_w wide survives at the
               rebate. Both flips are tried; the one that leaves the outer
               wall's top at shell_h - rim_slope_h is kept (predicate, R4).
  raised discs disc_h proud on the plate: stick_disc_d round the stick (the
               shaft hole and the four M3 holes stay open), btn_disc_d round
               each button. Annular profiles only, selected by loop count so
               no hole is filled.
  tyre ridges  two rings ridge_t proud and ridge_h tall on the outer wall at
               ridge_lo_z and ridge_hi_z: they locate the TPU tyre.
  port boss    a block joined inside the rear wall, then a flat facet_w wide
               cut across the outside at facet_y, leaving a flat wall
               boss_in thick for the port board (window is stage C).

Every feature is guarded by name so the script is idempotent in the document.
Stage A parameters must already exist with their stage A expressions.
"""
FH_ATTEMPT = 1
FH_OPTS = {
    "only_params": [
        "rim_slope_h", "rim_lip_w", "disc_h", "stick_disc_d", "btn_disc_d",
        "ridge_t", "ridge_h", "ridge_lo_z", "ridge_hi_z", "facet_w", "boss_in",
    ],
    "liveness_budget_s": 120,
}
INTERFERENCE_ALLOWED = []
CLEARANCES = []
from fusionhelper.buildkit import *

import adsk.core
import adsk.fusion

PARAMS_B = (
    ("rim_slope_h",   "7 mm",  "mm",  "rim band drop from the lip to the outer wall"),
    ("rim_lip_w",     "2 mm",  "mm",  "flat lip left beside the plate rebate"),
    ("rim_slope_w",   "(shell_dia - rebate_dia) / 2 - rim_lip_w", "mm", "derived: slope run"),
    ("rim_slope_ang", "atan(rim_slope_h / rim_slope_w)", "deg", "derived"),
    ("disc_h",        "2 mm",  "mm",  "raised discs on the plate"),
    ("stick_disc_d",  "90 mm", "mm",  "raised disc round the stick"),
    ("btn_disc_d",    "36 mm", "mm",  "raised disc round each button; 4 mm short of the 40 pitch"),
    ("ridge_t",       "0.8 mm", "mm", "tyre ridge proud of the wall"),
    ("ridge_h",       "2 mm",  "mm",  "tyre ridge height"),
    ("ridge_lo_z",    "5 mm",  "mm",  "lower tyre ridge, bottom face"),
    ("ridge_hi_z",    "41 mm", "mm",  "upper tyre ridge, bottom face"),
    ("ridge_od",      "shell_dia + 2 * ridge_t", "mm", "derived"),
    ("facet_w",       "64 mm", "mm",  "port facet chord width on the rear wall"),
    ("facet_y",       "sqrt((shell_dia / 2) ^ 2 - (facet_w / 2) ^ 2)", "mm", "derived: facet plane from the centre"),
    ("boss_in",       "8 mm",  "mm",  "flat wall thickness behind the facet"),
    # boss_w == facet_w and boss_y1 == facet_y: a wider or deeper boss pokes its
    # corners through the round wall into the tyre (measured 2026-09-12: 70 x
    # 0.75 x 34 mm clash with boss_w = facet_w + 6, boss_y1 = r - 1).
    ("boss_w",        "facet_w", "mm", "derived: boss exactly the facet chord"),
    ("boss_y0",       "facet_y - boss_in", "mm", "derived: boss inner face"),
    ("boss_y1",       "facet_y", "mm", "derived: boss outer face is the facet plane"),
)

BUTTONS = ("lp", "mp", "hp", "lk", "mk", "hk")
STAGE_A_ROOTS = ("shell_dia", "shell_h", "rebate_dia", "plate_t", "stick_x",
                 "stick_y", "stick_hole", "stick_bolt_r", "bolt_hole", "btn_hole",
                 "plate_top_z", "under_h", "floor_t")


def ensure_params(ctx):
    for name in STAGE_A_ROOTS:
        if ctx.up.itemByName(name) is None:
            raise RuntimeError("stage A parameter %s missing: run lap_disc.py first" % name)
    for name, expr, unit, comment in PARAMS_B:
        existing = ctx.up.itemByName(name)
        if existing is not None:
            if existing.expression.replace(" ", "") != expr.replace(" ", ""):
                raise RuntimeError(
                    "parameter %s already exists with expression %r, wanted %r"
                    % (name, existing.expression, expr))
            continue
        ctx.up.add(name, ctx.cbs(expr), unit, comment)
        adsk.doEvents()


def body_named(ctx, name):
    for b in ctx.root.bRepBodies:
        if b.name == name:
            return b
    raise RuntimeError("no body named %s" % name)


def feature_exists(ctx, name):
    """Sketches and features share one name namespace: a feature named like
    its sketch is auto-suffixed " (1)" (measured 2026-09-12), so both
    spellings are checked."""
    for coll in (ctx.extrudes, ctx.root.features.chamferFeatures):
        for n in (name, name + " (1)"):
            if coll.itemByName(n) is not None:
                return True
    return False


def centred_circle(ctx, sk, r_seed_cm, dia_expr, jitter):
    c = sk.sketchCurves.sketchCircles.addByCenterRadius(
        ctx.pt(0.011 + 0.003 * jitter, 0.017 + 0.005 * jitter, 0), r_seed_cm)
    sk.geometricConstraints.addCoincident(c.centerSketchPoint, sk.originPoint)
    d = sk.sketchDimensions.addDiameterDimension(c, ctx.pt(r_seed_cm + 0.4, -0.4, 0))
    d.parameter.expression = dia_expr
    return c


def concentric_circle(ctx, sk, ref_circle, r_seed_cm, dia_expr, jitter):
    """Second circle on an already-dimensioned centre: concentric + diameter."""
    rc = ref_circle.centerSketchPoint.geometry
    c = sk.sketchCurves.sketchCircles.addByCenterRadius(
        ctx.pt(rc.x + 0.004 * jitter, rc.y + 0.006 * jitter, 0), r_seed_cm)
    sk.geometricConstraints.addConcentric(ref_circle, c)
    d = sk.sketchDimensions.addDiameterDimension(
        c, ctx.pt(rc.x + r_seed_cm + 0.3, rc.y - 0.3, 0))
    d.parameter.expression = dia_expr
    return c


def axis_circle(ctx, sk, ref_circle, dx_cm, dy_cm, r_seed_cm, dia_expr,
                dist_expr, jitter):
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


def annular_profiles(sk):
    coll = adsk.core.ObjectCollection.create()
    n = 0
    for pr in sk.profiles:  # fusionhelper: allow R11 — collection add, not a document mutation
        if pr.profileLoops.count >= 2:
            coll.add(pr)
            n += 1
    if n == 0:
        raise RuntimeError("%s: no annular profile" % sk.name)
    return coll, n


def outer_wall_top_z(ctx, shell, r_cm):
    best = None
    for face in shell.faces:
        cyl = adsk.core.Cylinder.cast(face.geometry)
        if cyl is None or abs(cyl.radius - r_cm) > 0.005:
            continue
        z = face.boundingBox.maxPoint.z
        if best is None or z > best:
            best = z
    if best is None:
        raise RuntimeError("no cylindrical face of radius %.3f cm on the shell" % r_cm)
    return best


def run(_context: str):
    ctx = BuildCtx(adsk.core.Application.get())
    ensure_params(ctx)
    v = ctx.val
    shell = body_named(ctx, "shell")
    plate = body_named(ctx, "plate")
    r_out = v("shell_dia") / 2

    # ---- rim slope: chamfer on the outer top edge ------------------------
    if not feature_exists(ctx, "rim_slope"):
        edges = adsk.core.ObjectCollection.create()
        for e in shell.edges:
            circ = adsk.core.Circle3D.cast(e.geometry)
            if circ is None:
                continue
            if abs(circ.radius - r_out) < 0.005 and abs(circ.center.z - v("shell_h")) < 0.005:
                edges.add(e)
        if edges.count != 1:
            raise RuntimeError("expected one outer top edge, found %d" % edges.count)
        want_z = v("shell_h") - v("rim_slope_h")
        chamfers = ctx.root.features.chamferFeatures
        healthy = adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState
        done = False
        for flipped in (False, True):
            adsk.doEvents()
            ci = chamfers.createInput2()
            ci.chamferEdgeSets.addDistanceAndAngleChamferEdgeSet(
                edges, ctx.cbs("rim_slope_w"), ctx.cbs("rim_slope_ang"), flipped, False)
            f = chamfers.add(ci)
            shell = body_named(ctx, "shell")
            if f.healthState == healthy and abs(outer_wall_top_z(ctx, shell, r_out) - want_z) < 0.01:
                f.name = "rim_slope"
                done = True
                break
            f.deleteMe()
        if not done:
            raise RuntimeError("rim slope chamfer never left the outer wall top at %.2f cm" % want_z)
        shell = body_named(ctx, "shell")
        print("rim slope: outer wall top at %.2f mm, flipped=%s" % (outer_wall_top_z(ctx, shell, r_out) * 10, flipped))
    adsk.doEvents()

    # ---- raised discs on the plate ----------------------------------------
    if not feature_exists(ctx, "raised_discs"):
        plate_top = ctx.planes.itemByName("plate_top_plane")
        if plate_top is None:
            raise RuntimeError("plate_top_plane missing")
        sk = ctx.root.sketches.add(plate_top)
        sk.name = "raised_discs"
        z = v("plate_top_z")
        stick_in = ctx.bound_circle(
            sk, (v("stick_x"), v("stick_y"), z), v("stick_hole") / 2, "stick_hole",
            x_pos="abs(stick_x)", v_pos="abs(stick_y)")
        concentric_circle(ctx, sk, stick_in, v("stick_disc_d") / 2, "stick_disc_d", 1)
        br = v("stick_bolt_r")
        for k, (dx, dy) in enumerate(((br, 0), (-br, 0), (0, br), (0, -br))):
            axis_circle(ctx, sk, stick_in, dx, dy, v("bolt_hole") / 2, "bolt_hole",
                        "stick_bolt_r", k + 1)
        for i, name in enumerate(BUTTONS):
            inner = ctx.bound_circle(
                sk, (v(name + "_x"), v(name + "_y"), z), v("btn_hole") / 2, "btn_hole",
                x_pos="abs(%s_x)" % name, v_pos="abs(%s_y)" % name)
            concentric_circle(ctx, sk, inner, v("btn_disc_d") / 2, "btn_disc_d", i + 2)
            adsk.doEvents()
        if not sk.isFullyConstrained:
            loose = [i for i, c in enumerate(sk.sketchCurves.sketchCircles)
                     if not c.isFullyConstrained]
            raise RuntimeError("raised_discs loose circles: %s" % loose)
        profs, n = annular_profiles(sk)
        if n != 7:
            raise RuntimeError("raised_discs expected 7 annular profiles, got %d" % n)
        v0 = plate.volume
        f = ctx.checked_join(
            profs, "disc_h", plate,
            lambda b: b.volume - v0 > 1.4, "discs")
        f.name = "raised_discs"
        plate = body_named(ctx, "plate")
        print("raised discs: plate +%.2f cm3" % (plate.volume - v0))
    adsk.doEvents()

    # ---- tyre ridges on the outer wall -----------------------------------
    for tag, zp in (("lo", "ridge_lo_z"), ("hi", "ridge_hi_z")):
        name = "tyre_ridge_" + tag
        if feature_exists(ctx, name):
            continue
        pl = ctx.planes.itemByName(name + "_plane")
        if pl is None:
            pl = ctx.plane_at_z(zp, name + "_plane")
        sk = ctx.root.sketches.add(pl)
        sk.name = name
        inner = centred_circle(ctx, sk, r_out, "shell_dia", 1)
        concentric_circle(ctx, sk, inner, v("ridge_od") / 2, "ridge_od", 2)
        if not sk.isFullyConstrained:
            raise RuntimeError("%s sketch not fully constrained" % name)
        profs, n = annular_profiles(sk)
        if n != 1:
            raise RuntimeError("%s expected 1 annular profile, got %d" % (name, n))
        v0 = shell.volume
        f = ctx.checked_join(
            profs, "ridge_h", shell,
            lambda b: b.volume - v0 > 1.0, name)
        f.name = name
        shell = body_named(ctx, "shell")
        print("%s: shell +%.2f cm3" % (name, shell.volume - v0))
        adsk.doEvents()

    # ---- port boss inside the rear wall, then the flat facet --------------
    if not feature_exists(ctx, "port_boss"):
        fl = ctx.planes.itemByName("floor_plane")
        if fl is None:
            raise RuntimeError("floor_plane missing")
        sk = ctx.root.sketches.add(fl)
        sk.name = "port_boss"
        yc = (v("boss_y0") + v("boss_y1")) / 2
        ctx.bound_rect2(
            sk, (0, yc, v("floor_t")),
            v("boss_w") / 2, (v("boss_y1") - v("boss_y0")) / 2,
            u_size="boss_w", v_size="boss_y1 - boss_y0",
            u_pos=("0 mm", "boss_w / 2"), v_pos=("(boss_y0 + boss_y1) / 2", "(boss_y1 - boss_y0) / 2"))
        if not sk.isFullyConstrained:
            raise RuntimeError("port_boss sketch not fully constrained")
        v0 = shell.volume
        f = ctx.checked_join(
            ctx.all_profiles(sk), "under_h - floor_t", shell,
            lambda b: b.volume - v0 > 5.0, "boss")
        f.name = "port_boss"
        shell = body_named(ctx, "shell")
        print("port boss: shell +%.2f cm3" % (shell.volume - v0))
    adsk.doEvents()

    if not feature_exists(ctx, "port_facet"):
        sk = ctx.root.sketches.add(ctx.root.xYConstructionPlane)
        sk.name = "port_facet"
        y0 = v("facet_y")
        y1 = r_out + 1.0
        ctx.bound_rect2(
            sk, (0, (y0 + y1) / 2, 0),
            v("facet_w") / 2 + 1.0, (y1 - y0) / 2,
            u_size="facet_w + 20 mm", v_size="shell_dia / 2 + 10 mm - facet_y",
            u_pos=("0 mm", "(facet_w + 20 mm) / 2"),
            v_pos=("(facet_y + shell_dia / 2 + 10 mm) / 2", "(shell_dia / 2 + 10 mm - facet_y) / 2"))
        if not sk.isFullyConstrained:
            raise RuntimeError("port_facet sketch not fully constrained")
        f = ctx.blind_cut(ctx.all_profiles(sk), "shell_h + 1 mm", [shell], "facet",
                          min_vol_cm3=0.5)
        f.name = "port_facet"
        shell = body_named(ctx, "shell")
        flat = None
        for face in shell.faces:
            pln = adsk.core.Plane.cast(face.geometry)
            if pln is None:
                continue
            n = pln.normal
            if abs(n.y) > 0.999 and abs(face.boundingBox.maxPoint.y - y0) < 0.01:
                flat = face
        if flat is None:
            raise RuntimeError("no flat facet face at y = %.2f cm" % y0)
        bb = flat.boundingBox
        print("port facet: flat %.1f wide x %.1f tall at y %.2f mm" % (
            (bb.maxPoint.x - bb.minPoint.x) * 10, (bb.maxPoint.z - bb.minPoint.z) * 10, y0 * 10))
    adsk.doEvents()

    for b in (body_named(ctx, "shell"), body_named(ctx, "plate")):
        bb = b.boundingBox
        print("%s: %.3f x %.3f x %.3f mm, z %.3f..%.3f, %.2f cm3, %d faces" % (
            b.name,
            (bb.maxPoint.x - bb.minPoint.x) * 10,
            (bb.maxPoint.y - bb.minPoint.y) * 10,
            (bb.maxPoint.z - bb.minPoint.z) * 10,
            bb.minPoint.z * 10, bb.maxPoint.z * 10,
            b.volume, b.faces.count))
    print("done")
