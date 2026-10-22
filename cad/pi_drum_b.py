"""Pi console drum, D-021. Stage B -- four socket pads on the back half of
the base (plan task 4), in the document that holds stage A.

Each pad, at pad_ang_n from +x toward +y (the back is 90 deg):
  pad_n_flat    the wall cut flat at pad_r = sqrt(drum_r^2 - (pad_w/2)^2),
                a vertical flat pad_w wide from pad_z0 to pad_z1 -- the chord
                plane, so the sagitta is 1.42 at drum_r 80 / pad_w 30
  pad_n_back    a (pad_w + 4) x (pad_z1 - pad_z0 + 2) block joined inward
                pad_back_t from the chord plane, so the flange screws have
                a 5 mm flat-to-flat wall to bite
  pad_n_cut     the socket cutout <name>_cut_w x <name>_cut_h through the pad
  pad_n_pilot   two pilot_d x pilot_h pilots at +-<name>_screw_pitch / 2

Pads in angle order: RJ45 at 45, USB-C at 75, HDMI at 105, USB-A pair at
135 deg. The socket sizes are PLACEHOLDERS until the parts are measured
(OI-013); every one is a parameter.

How the flat, block and cutout are drawn (attempt 3, 2026-10-22): as
(r, z) rectangles on a RADIAL plane through the z axis at pad_ang_n
(sign probed, stage O's radial_plane_checked), extruded symmetrically
about that plane by the feature's width. The slab {r.n >= pad_r} x {|u| <=
pad_w/2} is exactly the chord region. Attempts 1-3 landed the rectangles
3 mm high in z (and, on the radial plane, at half the radius): the cause
was this script halving a compound size expression without parentheses
("pad_z1 - pad_z0 / 2"), not the kit. Every sketch's lines are mapped back
to model space and asserted against the intended r and z ranges BEFORE
the extrude, which is what pinned it down. The pilots are circles on the chord
plane (tangent plane offset by pad_r, sign probed); their landed centres
are asserted the same way.

Oracles: the flat removes the circular segment (r^2 acos(d/r) - d sqrt(r^2
- d^2)) x height; the block adds its box less the part already inside the
wall (integrated numerically); the cutout removes w x h x pad_back_t; the
pilots remove two cylinders. Containment reads back every pad.
"""
FH_ATTEMPT = 6
FH_OPTS = {
    "only_params": ["pad_w", "pad_back_t", "pad_z0", "pad_z1",
                    "pad_ang_1", "pad_ang_2", "pad_ang_3", "pad_ang_4",
                    "rj45_cut_w", "rj45_cut_h", "rj45_screw_pitch",
                    "usbc_cut_w", "usbc_cut_h", "usbc_screw_pitch",
                    "hdmi_cut_w", "hdmi_cut_h", "hdmi_screw_pitch",
                    "usba_cut_w", "usba_cut_h", "usba_screw_pitch",
                    "pilot_d", "pilot_h"],
    "liveness_budget_s": 400,
    "max_bodies": 1,
    "force_liveness": True,
}
INTERFERENCE_ALLOWED = []
CLEARANCES = []
# A screw pitch moves its two pilots symmetrically about the pad centre, so
# volume, area, face count, bbox and centroid are unchanged and the signature
# probe reads it as dead (stage A's intake_r precedent). prove_live steps each
# one and reads a pilot back.
EXPECT_DEAD = ["rj45_screw_pitch", "usbc_screw_pitch", "hdmi_screw_pitch", "usba_screw_pitch"]
from fusionhelper.buildkit import *

import adsk.core
import adsk.fusion
import math
import os

DOC_PREFIX = "arcade unit v1"
RENDER_DIR = r"C:/Users/gethi/sources/arcade-cabinet/.claude/worktrees/pi-drum/cad/renders"
PI = math.pi
MM = 0.1
TOL_MM = 0.05   # placement assertions

NEEDED = ("drum_d", "drum_r", "wall_t", "cavity_r", "floor_t", "split_z")
PARAMS = (
    ("pad_w",      "30 mm", "mm", "socket pad flat width"),
    ("pad_back_t", "5 mm",  "mm", "wall thickness behind a pad, flat to flat"),
    ("pad_z0",     "6 mm",  "mm", "pad bottom"),
    ("pad_z1",     "30 mm", "mm", "pad top"),
    ("pad_r",      "sqrt( drum_r ^ 2 - ( pad_w / 2 ) ^ 2 )", "mm", "derived: chord plane distance from the axis"),
    ("pad_ang_1",  "45 deg",  "deg", "RJ45 pad angle from +x toward +y"),
    ("pad_ang_2",  "75 deg",  "deg", "USB-C pad angle"),
    ("pad_ang_3",  "105 deg", "deg", "HDMI pad angle"),
    ("pad_ang_4",  "135 deg", "deg", "USB-A pair pad angle"),
    ("rj45_cut_w", "16 mm", "mm", "PLACEHOLDER (OI-013)"),
    ("rj45_cut_h", "14 mm", "mm", "PLACEHOLDER (OI-013)"),
    ("rj45_screw_pitch", "28 mm", "mm", "PLACEHOLDER (OI-013)"),
    ("usbc_cut_w", "10 mm", "mm", "PLACEHOLDER (OI-013)"),
    ("usbc_cut_h", "5 mm",  "mm", "PLACEHOLDER (OI-013)"),
    ("usbc_screw_pitch", "18 mm", "mm", "PLACEHOLDER (OI-013)"),
    ("hdmi_cut_w", "20 mm", "mm", "PLACEHOLDER (OI-013)"),
    ("hdmi_cut_h", "12 mm", "mm", "PLACEHOLDER (OI-013)"),
    ("hdmi_screw_pitch", "28 mm", "mm", "PLACEHOLDER (OI-013)"),
    ("usba_cut_w", "14 mm", "mm", "PLACEHOLDER (OI-013)"),
    ("usba_cut_h", "16 mm", "mm", "PLACEHOLDER (OI-013)"),
    ("usba_screw_pitch", "28 mm", "mm", "PLACEHOLDER (OI-013)"),
    ("pilot_d",    "2.5 mm", "mm", "flange screw pilot, M3 thread-forming"),
    ("pilot_h",    "4 mm",   "mm", "pilot depth from the pad; blind, 1 mm short of the block's inner face (6 broke through, measured)"),
)
PADS = (("rj45", "pad_ang_1", 45.0), ("usbc", "pad_ang_2", 75.0),
        ("hdmi", "pad_ang_3", 105.0), ("usba", "pad_ang_4", 135.0))


# ---------------------------------------------------------------- helpers (as stage A)

def ensure_params(ctx):
    for name in NEEDED:
        if ctx.up.itemByName(name) is None:
            raise RuntimeError("parameter %s missing: run stage A first" % name)
    for name, expr, unit, comment in PARAMS:
        existing = ctx.up.itemByName(name)
        if existing is not None:
            if existing.expression.replace(" ", "") != expr.replace(" ", ""):
                raise RuntimeError("parameter %s already exists with expression %r, wanted %r"
                                   % (name, existing.expression, expr))
            continue
        ctx.up.add(name, ctx.cbs(expr), unit, comment)
        adsk.doEvents()


def check_delta(label, before, after, want, tol_rel=0.02, tol_abs=0.002):
    got = after - before
    if abs(got - want) > max(tol_rel * abs(want), tol_abs):
        raise RuntimeError("%s: volume changed %.4f cm3, wanted %.4f" % (label, got, want))
    print("%s: %+.4f cm3 (want %+.4f)" % (label, got, want))


def healthy_or_raise(ctx, what):
    healthy = adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState
    tl = ctx.des.timeline
    bad = []
    for i in range(tl.count):
        it = tl.item(i)
        if it.isRolledBack:
            continue
        feat = adsk.fusion.Feature.cast(it.entity)
        if feat is not None and feat.healthState != healthy:
            bad.append("%s (%s)" % (feat.name, feat.errorOrWarningMessage))
    if bad:
        raise RuntimeError("after %s, unhealthy timeline entries: %s" % (what, bad))


def body_named(ctx, name):
    for b in ctx.root.bRepBodies:
        if b.name == name:
            return b
    raise RuntimeError("no body named %s" % name)


def inside(body, x_mm, y_mm, z_mm):
    return body.pointContainment(adsk.core.Point3D.create(x_mm * MM, y_mm * MM, z_mm * MM)) \
        == adsk.fusion.PointContainment.PointInsidePointContainment


def probe(body, pts, want_inside, label):
    for (x, y, z) in pts:
        if inside(body, x, y, z) != want_inside:
            raise RuntimeError("%s: (%.1f, %.1f, %.1f) should be %s" % (
                label, x, y, z, "solid" if want_inside else "empty"))
    print("%s: %d probes %s" % (label, len(pts), "solid" if want_inside else "empty"))


def radial_plane_checked(ctx, ang_expr, name, theta):
    """A plane through the z axis containing the direction theta; the sign of
    setByAngle is probed (R6), from stage O."""
    pt = ctx.pt(10 * math.cos(theta), 10 * math.sin(theta), 1.0)
    for e in (ang_expr, "-(%s)" % ang_expr):
        pin = ctx.planes.createInput()
        pin.setByAngle(ctx.root.zConstructionAxis, ctx.cbs(e), ctx.root.xZConstructionPlane)
        pl = ctx.planes.add(pin)
        pl.name = name
        sk = ctx.root.sketches.add(pl)
        off = abs(sk.modelToSketchSpace(pt).z)
        sk.deleteMe()
        if off < 0.01:
            return pl
        pl.deleteMe()
        adsk.doEvents()
    raise RuntimeError("radial plane %s never contained the probe point" % name)


def chord_plane_checked(ctx, tangent_plane, dist_expr, name, theta, r_cm):
    """tangent_plane offset by dist_expr so it passes through (r cos, r sin, z);
    the offset sign is probed."""
    pt = ctx.pt(r_cm * math.cos(theta), r_cm * math.sin(theta), 1.5)
    for e in (dist_expr, "-(%s)" % dist_expr):
        pin = ctx.planes.createInput()
        pin.setByOffset(tangent_plane, ctx.cbs(e))
        pl = ctx.planes.add(pin)
        pl.name = name
        sk = ctx.root.sketches.add(pl)
        off = abs(sk.modelToSketchSpace(pt).z)
        sk.deleteMe()
        if off < 0.01:
            return pl
        pl.deleteMe()
        adsk.doEvents()
    raise RuntimeError("chord plane %s never passed through the probe point" % name)


# ---------------------------------------------------------------- sketch recipes

def radial_rect(ctx, sk, theta, r_c, z_c, r_half, z_half, r_size, r_pos, z_size, z_pos):
    """(r, z) rectangle on a radial plane, from stage O. cm seeds, mm expressions."""
    ctx.U = (math.cos(theta), math.sin(theta), 0.0)
    ctx.V = (0.0, 0.0, 1.0)
    try:
        # The half-size is a compound expression: parenthesise it, or
        # "pad_z1 - pad_z0 / 2" halves the wrong term (measured 2026-10-22:
        # the rectangle landed at z 9..33 and r 38..40.5 for exactly that).
        ctx.bound_rect2(sk, (r_c * math.cos(theta), r_c * math.sin(theta), z_c), r_half, z_half,
                        u_size=r_size, v_size=z_size,
                        u_pos=(r_pos, "( %s ) / 2" % r_size), v_pos=(z_pos, "( %s ) / 2" % z_size))
    finally:
        ctx.U = (1.0, 0.0, 0.0)
        ctx.V = (0.0, 1.0, 0.0)


def assert_rect_landed(sk, theta, r_lo, r_hi, z_lo, z_hi, label):
    """Map the sketch's line endpoints to model space and check the r (along
    the radial direction) and z ranges, mm."""
    n = (math.cos(theta), math.sin(theta))
    rs, zs = [], []
    for i in range(sk.sketchCurves.sketchLines.count):
        ln = sk.sketchCurves.sketchLines.item(i)
        for p in (ln.startSketchPoint.geometry, ln.endSketchPoint.geometry):
            m = sk.sketchToModelSpace(p)
            rs.append((m.x * n[0] + m.y * n[1]) * 10)
            zs.append(m.z * 10)
    got = (min(rs), max(rs), min(zs), max(zs))
    want = (r_lo, r_hi, z_lo, z_hi)
    if any(abs(g - w) > TOL_MM for g, w in zip(got, want)):
        raise RuntimeError("%s: rectangle landed r %.2f..%.2f z %.2f..%.2f, wanted r %.2f..%.2f z %.2f..%.2f"
                           % ((label,) + got + want))
    print("%s: rectangle at r %.2f..%.2f z %.2f..%.2f" % ((label,) + got))


def sym_cut_checked(ctx, sk, width_expr, body, want, label, min_vol=0.01):
    v0 = body.volume
    f = ctx.sym_cut(ctx.all_profiles(sk), width_expr, [body], min_vol_cm3=min_vol)
    f.name = label
    check_delta(label, v0, body.volume, -want, tol_rel=0.02)
    return f


def sym_join_checked(ctx, sk, width_expr, body, want, label):
    v0 = body.volume
    inp = ctx.extrudes.createInput(ctx.all_profiles(sk), ctx.ops.JoinFeatureOperation)
    inp.setSymmetricExtent(ctx.cbs(width_expr), True)
    inp.participantBodies = [body]
    f = ctx.extrudes.add(inp)
    f.name = label
    check_delta(label, v0, body.volume, want, tol_rel=0.03)
    return f


def tangent_circle(ctx, sk, theta, r_c, z_c, u_off_cm, r_seed, dia_expr, u_expr, z_expr):
    ctx.U = (-math.sin(theta), math.cos(theta), 0.0)
    try:
        w = (r_c * math.cos(theta) - u_off_cm * math.sin(theta),
             r_c * math.sin(theta) + u_off_cm * math.cos(theta), z_c)
        return ctx.bound_circle(sk, w, r_seed, dia_expr, x_pos=u_expr, v_pos=z_expr)
    finally:
        ctx.U = (1.0, 0.0, 0.0)


def assert_circle_landed(sk, circle, theta, u_want, z_want, label):
    m = sk.sketchToModelSpace(circle.centerSketchPoint.geometry)
    u = (-m.x * math.sin(theta) + m.y * math.cos(theta)) * 10
    z = m.z * 10
    if abs(u - u_want) > TOL_MM or abs(z - z_want) > TOL_MM:
        raise RuntimeError("%s: circle landed u %.2f z %.2f, wanted u %.2f z %.2f" % (label, u, z, u_want, z_want))
    print("%s: circle at u %.2f z %.2f" % (label, u, z))


# ---------------------------------------------------------------- oracles

def segment_area(r, d):
    """Area between a chord at distance d from the centre and the arc."""
    return r * r * math.acos(d / r) - d * math.sqrt(r * r - d * d)


def block_added(ctx, half_u, h):
    """Volume a block (2 half_u wide, h tall, from the chord plane at pad_r
    inward pad_back_t) adds to the wall: its box less the part already
    inside the wall, which lies between the inner-wall circle (cavity_r)
    and the chord plane. cm."""
    v = ctx.val
    pad_r, t, ri = v("pad_r"), v("pad_back_t"), v("cavity_r")
    n = 400
    overlap = 0.0
    for i in range(n):
        u = -half_u + (i + 0.5) * (2 * half_u / n)
        r_in = math.sqrt(ri * ri - u * u) if abs(u) < ri else 0.0
        overlap += max(0.0, pad_r - max(r_in, pad_r - t)) * (2 * half_u / n)
    return (2 * half_u * t - overlap) * h


# ---------------------------------------------------------------- build

def build_pad(ctx, base, name, ang_param, theta_deg):
    v = ctx.val
    th = math.radians(theta_deg)
    pad_r, dr, w, t = v("pad_r"), v("drum_r"), v("pad_w"), v("pad_back_t")
    z0, z1 = v("pad_z0"), v("pad_z1")
    h, zc = z1 - z0, (z0 + z1) / 2
    mm = lambda cm: cm * 10  # noqa: E731

    radial = radial_plane_checked(ctx, ang_param, "pad_%s_radial" % name, th)

    # the flat: (r, z) rectangle from pad_r to drum_r + 1, z0..z1, symmetric pad_w wide
    sk = ctx.root.sketches.add(radial)
    sk.name = "pad_%s_flat_sk" % name
    r_hi = dr + 0.1
    radial_rect(ctx, sk, th, (pad_r + r_hi) / 2, zc, (r_hi - pad_r) / 2, h / 2,
                "drum_r + 1 mm - pad_r", "( pad_r + drum_r + 1 mm ) / 2", "pad_z1 - pad_z0", "( pad_z0 + pad_z1 ) / 2")
    assert_rect_landed(sk, th, mm(pad_r), mm(r_hi), mm(z0), mm(z1), "pad_%s_flat" % name)
    sym_cut_checked(ctx, sk, "pad_w", base, segment_area(dr, pad_r) * h, "pad_%s_flat" % name)

    # the block behind it: from pad_r - t to pad_r, z0-1..z1+1, symmetric pad_w + 4 wide
    sk = ctx.root.sketches.add(radial)
    sk.name = "pad_%s_back_sk" % name
    radial_rect(ctx, sk, th, pad_r - t / 2, zc, t / 2, h / 2 + 0.1,
                "pad_back_t", "pad_r - pad_back_t / 2", "pad_z1 - pad_z0 + 2 mm", "( pad_z0 + pad_z1 ) / 2")
    assert_rect_landed(sk, th, mm(pad_r - t), mm(pad_r), mm(z0) - 1, mm(z1) + 1, "pad_%s_back" % name)
    sym_join_checked(ctx, sk, "pad_w + 4 mm", base, block_added(ctx, w / 2 + 0.2, h + 0.2), "pad_%s_back" % name)

    # the socket cutout: from pad_r - t - 1 to pad_r + 1, cut_h tall, symmetric cut_w wide
    sk = ctx.root.sketches.add(radial)
    sk.name = "pad_%s_cut_sk" % name
    cw, chh = v("%s_cut_w" % name), v("%s_cut_h" % name)
    radial_rect(ctx, sk, th, pad_r - t / 2, zc, t / 2 + 0.1, chh / 2,
                "pad_back_t + 2 mm", "pad_r - pad_back_t / 2", "%s_cut_h" % name, "( pad_z0 + pad_z1 ) / 2")
    assert_rect_landed(sk, th, mm(pad_r - t) - 1, mm(pad_r) + 1, mm(zc - chh / 2), mm(zc + chh / 2), "pad_%s_cut" % name)
    sym_cut_checked(ctx, sk, "%s_cut_w" % name, base, cw * chh * t, "pad_%s_cut" % name)

    # the pilots: circles on the chord plane at +-pitch/2 along the tangent
    tangent = radial_plane_checked(ctx, "%s + 90 deg" % ang_param, "pad_%s_tangent" % name, th + PI / 2)
    chord = chord_plane_checked(ctx, tangent, "pad_r", "pad_%s_chord" % name, th, pad_r)
    sk = ctx.root.sketches.add(chord)
    sk.name = "pad_%s_pilot_sk" % name
    pitch = v("%s_screw_pitch" % name)
    for sgn in (1, -1):
        c = tangent_circle(ctx, sk, th, pad_r, zc, sgn * pitch / 2, v("pilot_d") / 2, "pilot_d",
                           "%s_screw_pitch / 2" % name, "( pad_z0 + pad_z1 ) / 2")
        assert_circle_landed(sk, c, th, sgn * mm(pitch) / 2, mm(zc), "pad_%s_pilot" % name)
        adsk.doEvents()
    v0 = base.volume
    f = ctx.blind_cut(ctx.all_profiles(sk), "pilot_h", [base], "pilot_%s" % name, min_vol_cm3=0.003)
    f.name = "pad_%s_pilot" % name
    check_delta("pad_%s_pilot" % name, v0, base.volume, -2 * PI * (v("pilot_d") / 2) ** 2 * v("pilot_h"),
                tol_rel=0.03, tol_abs=0.001)


def read_back(ctx, base):
    v = ctx.val
    pad_r, t = v("pad_r") * 10, v("pad_back_t") * 10
    zc = (v("pad_z0") + v("pad_z1")) * 5
    for name, _, theta_deg in PADS:
        th = math.radians(theta_deg)
        tan = (-math.sin(th), math.cos(th))
        cw, pitch = v("%s_cut_w" % name) * 10, v("%s_screw_pitch" % name) * 10

        def at(r, u, z):
            return (r * math.cos(th) + u * tan[0], r * math.sin(th) + u * tan[1], z)
        probe(base, [at(pad_r + 0.7, 0, zc), at(pad_r + 0.7, cw / 2 + 2, zc)], False, "pad %s: outside the flat" % name)
        probe(base, [at(pad_r - 1, 0, zc), at(pad_r - t + 0.5, 0, zc)], False, "pad %s: cutout open through" % name)
        probe(base, [at(pad_r - 1, cw / 2 + 2, zc), at(pad_r - t + 0.5, cw / 2 + 2, zc)], True, "pad %s: block beside the cutout" % name)
        probe(base, [at(pad_r - t - 1.5, cw / 2 + 2, zc)], False, "pad %s: cavity behind the block" % name)
        probe(base, [at(pad_r - 2, pitch / 2, zc), at(pad_r - 2, -pitch / 2, zc)], False, "pad %s: pilots" % name)
        probe(base, [at(pad_r - 2, pitch / 2 + 2.5, zc)], True, "pad %s: beside a pilot" % name)
        probe(base, [at(pad_r - 1, 0, v("pad_z0") * 10 - 2), at(pad_r - 1, 0, v("pad_z1") * 10 + 1.5)], True,
              "pad %s: wall below and above the flat" % name)
    probe(base, [(0, -78.5, 20), (78.5, 0, 20)], True, "front and right wall intact")


def prove_live(ctx, name, stepped_expr, point_mm, restore_expr):
    """Step a parameter the signature probe cannot see, check that a point
    which was empty (a pilot centre) becomes solid, and restore. The body is
    re-resolved by name after every write (R5)."""
    base = body_named(ctx, "base")
    if inside(base, *point_mm):
        raise RuntimeError("prove_live %s: probe point should start empty" % name)
    ctx.up.itemByName(name).expression = stepped_expr  # fusionhelper: allow R5 — body re-resolved by name after the write
    adsk.doEvents()
    base = body_named(ctx, "base")
    moved = inside(base, *point_mm)
    ctx.up.itemByName(name).expression = restore_expr  # fusionhelper: allow R5 — body re-resolved by name after the write
    adsk.doEvents()
    if not moved:
        raise RuntimeError("prove_live %s: pilot did not move when stepped to %s" % (name, stepped_expr))
    healthy_or_raise(ctx, "prove_live " + name)
    print("prove_live %s: stepped to %s, pilot moved, restored to %s" % (name, stepped_expr, restore_expr))


def prove_symmetric_params(ctx):
    v = ctx.val
    r_probe = v("pad_r") * 10 - 2
    zc = (v("pad_z0") + v("pad_z1")) * 5
    for name, _, theta_deg in PADS:
        th = math.radians(theta_deg)
        pname = "%s_screw_pitch" % name
        pitch = v(pname) * 10
        u = pitch / 2
        pt = (r_probe * math.cos(th) - u * math.sin(th), r_probe * math.sin(th) + u * math.cos(th), zc)
        prove_live(ctx, pname, "%g mm" % (pitch + 4), pt, "%g mm" % pitch)


def render(ctx, tag):
    os.makedirs(RENDER_DIR, exist_ok=True)
    vp = ctx.app.activeViewport
    for name, orient in (("rear", adsk.core.ViewOrientations.BackViewOrientation),
                         ("iso", adsk.core.ViewOrientations.IsoTopLeftViewOrientation)):
        cam = vp.camera
        cam.viewOrientation = orient
        cam.isFitView = True
        vp.camera = cam
        adsk.doEvents()
        vp.saveAsImageFile(os.path.join(RENDER_DIR, "pi_drum_stage%s_%s.png" % (tag, name)), 1600, 1200)


def run(_context: str):
    app = adsk.core.Application.get()
    if not app.activeDocument.name.startswith(DOC_PREFIX):
        raise RuntimeError("wrong document %r" % app.activeDocument.name)
    ctx = BuildCtx(app)
    ensure_params(ctx)
    base = body_named(ctx, "base")
    for name, ang_param, theta in PADS:
        build_pad(ctx, base, name, ang_param, theta)
        base = body_named(ctx, "base")
        adsk.doEvents()
    healthy_or_raise(ctx, "stage B")
    base = body_named(ctx, "base")
    read_back(ctx, base)
    prove_symmetric_params(ctx)
    base = body_named(ctx, "base")
    if ctx.root.bRepBodies.count != 1:
        raise RuntimeError("expected 1 body, found %d" % ctx.root.bRepBodies.count)
    print("base: %.4f cm3, %d faces" % (base.volume, base.faces.count))
    render(ctx, "B")
    print("done")
