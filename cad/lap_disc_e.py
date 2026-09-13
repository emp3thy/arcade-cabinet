"""Lap pad, D-014: the nested disc. Stage E -- the tyre meets the port facet,
in the document that holds stages A to D.

The stage B facet cuts a flat facet_w wide across the rear wall at facet_y,
full height. The wall's outer radius is shell_dia / 2, so between the flat
and the tyre's round inner face there was a lens-shaped gap, shell_dia / 2 -
facet_y (3.8 mm) wide at x = 0, open from the floor to the rim slope: the
"hole" seen from above on 2026-09-13. The port behind the facet is the
charging input, so it must stay reachable from outside (owner, same day).
Two features on the tpu_tyre body:

  tyre_fill    JOIN the lens between the facet chord and the shell circle,
               tyre_z0 to ridge_hi_z (the tyre's own height). Profile: the
               piece of a rectangle (facet_w + 16 mm wide, from facet_y
               outward past the circle) that lies inside a shell_dia circle,
               picked by centroid and area, not by index (R4). No new root:
               the arc bounds it whatever the rectangle's depth.
  tyre_window  CUT a tyre_win_w x tyre_win_h window through the filled tyre
               from the facet plane outward, in line with the stage C
               port_window (centre x = 0, z = port_cz). tyre_win_clear a
               side over the port window. TPU bridges above and below the
               window are about 3 mm; the tyre is a stretched O-ring, so
               they carry tension.

Oracles: tyre_fill adds exactly the segment area (R^2 (t - sin t cos t),
t = acos(facet_y / R)) times tyre_h; tyre_window removes the integral of
(sqrt(Ro^2 - x^2) - facet_y) over the window width, times its height, LESS
the material the stage D tyre_r fillets had already taken off the outer
corners inside the window's height (attempt 1 measured the cut 2.6 % short
of the plain prism: the window's top and bottom edges sit inside the
fillet zones). The window feature is rebuilt on every run so the oracle
always sees the cut it checks.

Still not modelled: port-board M3 holes (ASSUMED 24 x 20), rim-band
lettering, raised-disc colour split. Open: an external charging port
contradicts D-010 / D-014 (Qi only, no reachable USB-C) -- decision log
entry needed, owner's call.
"""
FH_ATTEMPT = 2
FH_OPTS = {
    "only_params": ["tyre_win_clear"],
    "liveness_budget_s": 120,
}
INTERFERENCE_ALLOWED = []
CLEARANCES = []
EXPECT_DEAD = []  # namespace is reused across executes
from fusionhelper.buildkit import *

import adsk.core
import adsk.fusion
import math

PARAMS_E = (
    ("tyre_win_clear", "0.5 mm", "mm", "tyre window clearance a side over the port window"),
    ("tyre_win_w", "port_w + 2 * tyre_win_clear", "mm", "derived"),
    ("tyre_win_h", "port_h + 2 * tyre_win_clear", "mm", "derived"),
    ("fill_depth", "shell_dia / 2 - facet_y + 5 mm", "mm", "derived: fill rectangle from the facet past the shell circle"),
    ("fill_w", "facet_w + 16 mm", "mm", "derived: fill rectangle wider than the facet chord"),
)

NEEDED = ("shell_dia", "facet_w", "facet_y", "tyre_z0", "tyre_h", "ridge_hi_z",
          "tyre_od", "tyre_r", "port_w", "port_h", "port_cz")


def ensure_params(ctx):
    for name in NEEDED:
        if ctx.up.itemByName(name) is None:
            raise RuntimeError("parameter %s missing: run stages A to D first" % name)
    for name, expr, unit, comment in PARAMS_E:
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
    for n in (name, name + " (1)"):
        if ctx.extrudes.itemByName(n) is not None:
            return True
    return False


def centred_circle(ctx, sk, r_seed_cm, dia_expr, jitter):
    c = sk.sketchCurves.sketchCircles.addByCenterRadius(
        ctx.pt(0.011 + 0.003 * jitter, 0.017 + 0.005 * jitter, 0), r_seed_cm)
    sk.geometricConstraints.addCoincident(c.centerSketchPoint, sk.originPoint)
    d = sk.sketchDimensions.addDiameterDimension(c, ctx.pt(r_seed_cm + 0.4, -0.4, 0))
    d.parameter.expression = dia_expr
    return c


def segment_profile(sk, facet_y_cm, max_area_cm2):
    """The one profile whose centroid lies beyond the facet chord and whose
    area is small: the circle segment, not the rectangle's outer remainder
    and not the rest of the disc (R4: predicate, not index)."""
    coll = adsk.core.ObjectCollection.create()
    found = []
    for pr in sk.profiles:  # fusionhelper: allow R11 — collection add, not a document mutation
        props = pr.areaProperties(adsk.fusion.CalculationAccuracy.HighCalculationAccuracy)
        c = sk.sketchToModelSpace(props.centroid)
        found.append((round(props.area, 3), round(c.y * 10, 2)))
        if c.y > facet_y_cm and props.area < max_area_cm2:
            coll.add(pr)
    if coll.count != 1:
        raise RuntimeError("segment profile: want 1, matched %d; profiles (area cm2, centroid y mm): %s"
                           % (coll.count, found))
    return coll


def segment_area_cm2(R, d):
    t = math.acos(d / R)
    return R * R * (t - math.sin(t) * math.cos(t))


def window_volume_cm3(Ro, d, half_w, h, n=400):
    """Integral of (sqrt(Ro^2 - x^2) - d) dx over [-half_w, half_w], times h."""
    s = 0.0
    dx = 2 * half_w / n
    for i in range(n):
        x = -half_w + (i + 0.5) * dx
        s += math.sqrt(Ro * Ro - x * x) - d
    return s * dx * h


def fillet_deficit_cm3(r_f, gap, Ro, half_w):
    """Material a radius-r_f round on the tyre's outer edge had already
    removed within the window: the corner strip from the window's edge
    (gap from the tyre's edge) to the tyre's edge, integrated over the
    arc the window spans at Ro. Zero when the window clears the fillet."""
    u1 = max(0.0, min(r_f, r_f - gap))
    if u1 <= 0:
        return 0.0
    area = r_f * u1 - (u1 / 2 * math.sqrt(r_f * r_f - u1 * u1) + r_f * r_f / 2 * math.asin(u1 / r_f))
    arc = 2 * Ro * math.asin(half_w / Ro)
    return area * arc


def run(_context: str):
    ctx = BuildCtx(adsk.core.Application.get())
    ensure_params(ctx)
    v = ctx.val
    tyre = body_named(ctx, "tpu_tyre")
    R = v("shell_dia") / 2
    d = v("facet_y")

    # ---- tyre fill: the lens between the facet chord and the shell circle ----
    if not feature_exists(ctx, "tyre_fill"):
        pl = ctx.planes.itemByName("tyre_plane")
        if pl is None:
            raise RuntimeError("tyre_plane missing")
        sk = ctx.root.sketches.add(pl)
        sk.name = "tyre_fill"
        centred_circle(ctx, sk, R, "shell_dia", 1)
        fd = v("fill_depth")
        ctx.bound_rect2(
            sk, (0, d + fd / 2, v("tyre_z0")),
            v("fill_w") / 2, fd / 2,
            u_size="fill_w", v_size="fill_depth",
            u_pos=("0 mm", "fill_w / 2"), v_pos=("facet_y + fill_depth / 2", "fill_depth / 2"))
        if not sk.isFullyConstrained:
            raise RuntimeError("tyre_fill sketch not fully constrained")
        want = segment_area_cm2(R, d) * v("tyre_h")
        profs = segment_profile(sk, d, 3.0)
        v0 = tyre.volume
        f = ctx.checked_join(profs, "tyre_h", tyre,
                             lambda b: abs((b.volume - v0) - want) < 0.02 * want, "fill")
        f.name = "tyre_fill"
        tyre = body_named(ctx, "tpu_tyre")
        bb = tyre.boundingBox
        if abs(bb.minPoint.z - v("tyre_z0")) > 0.01 or abs(bb.maxPoint.z - v("ridge_hi_z")) > 0.01:
            raise RuntimeError("tyre_fill changed the tyre's z range: %.2f..%.2f" % (bb.minPoint.z, bb.maxPoint.z))
        print("tyre fill: +%.4f cm3 (want %.4f), tyre z %.1f..%.1f mm" % (
            tyre.volume - v0, want, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    adsk.doEvents()

    # ---- tyre window, in line with the port window ----------------------------
    # Rebuilt every run: attempt 1 left a window whose oracle was wrong, and
    # the only way to re-check a cut's volume is to make it again.
    old = ctx.extrudes.itemByName("tyre_window")
    if old is not None:
        old.deleteMe()
        adsk.doEvents()
    old_sk = ctx.root.sketches.itemByName("tyre_window")
    if old_sk is not None:
        old_sk.deleteMe()
        adsk.doEvents()
    tyre = body_named(ctx, "tpu_tyre")
    if True:
        pl = ctx.planes.itemByName("facet_plane")
        if pl is None:
            raise RuntimeError("facet_plane missing")
        sk = ctx.root.sketches.add(pl)
        sk.name = "tyre_window"
        ctx.V = (0.0, 0.0, 1.0)
        ctx.bound_rect2(
            sk, (0, d, v("port_cz")),
            v("tyre_win_w") / 2, v("tyre_win_h") / 2,
            u_size="tyre_win_w", v_size="tyre_win_h",
            u_pos=("0 mm", "tyre_win_w / 2"), v_pos=("port_cz", "tyre_win_h / 2"))
        ctx.V = (0.0, 1.0, 0.0)
        if not sk.isFullyConstrained:
            raise RuntimeError("tyre_window sketch not fully constrained")
        Ro, hw = v("tyre_od") / 2, v("tyre_win_w") / 2
        z_lo, z_hi = v("port_cz") - v("tyre_win_h") / 2, v("port_cz") + v("tyre_win_h") / 2
        want = (window_volume_cm3(Ro, d, hw, v("tyre_win_h"))
                - fillet_deficit_cm3(v("tyre_r"), z_lo - v("tyre_z0"), Ro, hw)
                - fillet_deficit_cm3(v("tyre_r"), v("ridge_hi_z") - z_hi, Ro, hw))
        v0 = tyre.volume
        f = ctx.blind_cut(ctx.all_profiles(sk), "tyre_od / 2 - facet_y + 2 mm", [tyre],
                          "tyre_win", min_vol_cm3=0.5 * want)
        f.name = "tyre_window"
        tyre = body_named(ctx, "tpu_tyre")
        removed = v0 - tyre.volume
        if abs(removed - want) > 0.02 * want:
            raise RuntimeError("tyre_window removed %.4f cm3, wanted %.4f" % (removed, want))
        print("tyre window: -%.4f cm3 (want %.4f)" % (removed, want))
    adsk.doEvents()

    # ---- read-back: the lens is closed where the tyre stands ------------------
    P = adsk.core.Point3D.create
    inside = adsk.fusion.PointContainment.PointInsidePointContainment
    y_mid = (d + R) / 2
    z_mid = (v("tyre_z0") + v("ridge_hi_z")) / 2
    if tyre.pointContainment(P(2.5, y_mid, z_mid)) != inside:
        raise RuntimeError("lens at x=25 mm still open inside the tyre")
    if tyre.pointContainment(P(0, y_mid, v("port_cz"))) == inside:
        raise RuntimeError("tyre window did not open the port line")
    print("lens closed at x=25 mm, open on the port axis at z=%.1f mm" % (v("port_cz") * 10))

    tl = ctx.des.timeline
    bad = []
    for i in range(tl.count):
        feat = adsk.fusion.Feature.cast(tl.item(i).entity)
        if feat is not None and feat.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState:
            bad.append(feat.name)
    if bad:
        raise RuntimeError("unhealthy timeline entries: %s" % bad)

    for name in ("shell", "plate", "tpu_ring", "tpu_tyre"):
        b = body_named(ctx, name)
        bb = b.boundingBox
        print("%s: %.1f x %.1f x %.1f mm, z %.1f..%.1f, %.2f cm3, %d faces" % (
            b.name,
            (bb.maxPoint.x - bb.minPoint.x) * 10,
            (bb.maxPoint.y - bb.minPoint.y) * 10,
            (bb.maxPoint.z - bb.minPoint.z) * 10,
            bb.minPoint.z * 10, bb.maxPoint.z * 10,
            b.volume, b.faces.count))
    print("done")
