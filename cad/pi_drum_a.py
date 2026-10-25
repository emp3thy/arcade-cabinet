"""Pi console drum, D-021. Stage A -- the base tray, in a fresh document
named "Pi Console Drum" (spec docs/superpowers/specs/2026-10-21-pi-console-drum-design.md,
plan task 3).

Frame: origin on the drum axis at the underside, x to the player's right,
y toward the back, z up.

  base_floor     disc drum_d x floor_t, z 0..floor_t, new body "base"
  base_wall      ring drum_d / 2 cavity_r, floor_t..split_z, joined
  floor_channel  one chan_w x chan_d channel in the underside from chan_r0
                 to past the rim along +x, then a circular pattern of chan_n
  intake_holes   two intake_d holes per channel at intake_r1 and intake_r2,
                 drawn explicitly with cos/sin position expressions
  pi_boss        four pi_boss_d x pi_boss_h bosses on the floor at
                 (+-pi_hole_px/2, +-pi_hole_py/2), joined
  pi_insert      pi_insert_hole x pi_insert_h holes down from the boss tops
  base_screw     four screw_clear_d holes countersunk csk_d x 90 deg from the
                 underside at col_r on +-20 and +-160 deg, through the floor

Oracles: every feature asserts its analytic volume change; the channel and
hole patterns are validated by face count (volume is a poor oracle for
small holes, measured); point containment reads back every hole and boss.
Negative coordinates: a distance dimension is unsigned, so circle position
expressions are wrapped in abs() and the jittered seed is placed on the
signed side; the read-back probes the SIGNED coordinates.
"""
FH_ATTEMPT = 1
FH_OPTS = {
    "only_params": ["drum_d", "wall_t", "floor_t", "split_z",
                    "chan_n", "chan_w", "chan_d", "chan_r0",
                    "intake_d", "intake_r1", "intake_r2",
                    "pi_hole_px", "pi_hole_py", "pi_boss_d", "pi_boss_h",
                    "pi_insert_hole", "pi_insert_h",
                    "col_r", "screw_clear_d", "csk_d"],
    "liveness_budget_s": 300,
    "max_bodies": 1,
}
INTERFERENCE_ALLOWED = []
CLEARANCES = []
# These four move holes symmetrically about the axis: volume, area, face
# count, bbox and centroid stay byte-identical, so the signature probe
# reads them as dead (the pad's stick_bolt_r precedent). They are live:
# prove_live steps each one and reads a hole back.
EXPECT_DEAD = ["intake_r1", "intake_r2", "pi_hole_px", "pi_hole_py"]
from fusionhelper.buildkit import *

import adsk.core
import adsk.fusion
import math
import os

DOC_PREFIX = "arcade unit v1"   # the owner's name for the drum document (2026-10-22)
RENDER_DIR = r"C:/Users/gethi/sources/arcade-cabinet/.claude/worktrees/pi-drum/cad/renders"
PI = math.pi
MM = 0.1   # cm per mm, seeds only

PARAMS = (
    # (name, expression, unit, comment)
    ("drum_d",         "160 mm", "mm", "drum outside diameter"),
    ("wall_t",         "3 mm",   "mm", "wall, both parts"),
    ("floor_t",        "3 mm",   "mm", "base floor"),
    ("split_z",        "32 mm",  "mm", "parting line, base top / cup bottom"),
    ("drum_r",         "drum_d / 2", "mm", "derived"),
    ("cavity_r",       "drum_r - wall_t", "mm", "derived"),
    ("chan_n",         "8",      "",   "underside air channels, 45 deg steps from +x"),
    ("chan_w",         "12 mm",  "mm", "channel width"),
    ("chan_d",         "2 mm",   "mm", "channel depth into the underside"),
    ("chan_r0",        "50 mm",  "mm", "channel inner end radius"),
    ("intake_d",       "5 mm",   "mm", "intake hole diameter"),
    ("intake_r1",      "58 mm",  "mm", "inner intake hole radius, on the channel lines"),
    ("intake_r2",      "68 mm",  "mm", "outer intake hole radius"),
    ("pi_hole_px",     "58 mm",  "mm", "Pi 4B hole pitch along x"),
    ("pi_hole_py",     "49 mm",  "mm", "Pi 4B hole pitch along y"),
    ("pi_boss_d",      "6 mm",   "mm", "Pi standoff boss diameter"),
    ("pi_boss_h",      "5 mm",   "mm", "Pi standoff boss height above the floor"),
    ("pi_insert_hole", "3.4 mm", "mm", "M2.5 heat-set insert bore (placeholder, owner's inserts)"),
    ("pi_insert_h",    "4 mm",   "mm", "insert bore depth"),
    ("col_r",          "72.8 mm", "mm", "cup column centre radius; the base screws sit under them"),
    ("screw_clear_d",  "3.4 mm", "mm", "M3 clearance"),
    ("csk_d",          "6.5 mm", "mm", "90 deg countersink diameter for M3 flat heads"),
)
COL_ANGLES = (20.0, 160.0, -160.0, -20.0)          # degrees, from +x toward +y
PI_HOLES = ((1, 1), (-1, 1), (-1, -1), (1, -1))     # signs of (px/2, py/2)


# ---------------------------------------------------------------- helpers

def ensure_params(ctx):
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


def centred_circle(ctx, sk, r_seed_cm, dia_expr, jitter):
    """Circle pinned to the sketch origin by a coincident constraint and a
    bound diameter (from cad/lap_disc.py)."""
    c = sk.sketchCurves.sketchCircles.addByCenterRadius(
        ctx.pt(0.011 + 0.003 * jitter, 0.017 + 0.005 * jitter, 0), r_seed_cm)
    sk.geometricConstraints.addCoincident(c.centerSketchPoint, sk.originPoint)
    d = sk.sketchDimensions.addDiameterDimension(c, ctx.pt(r_seed_cm + 0.4, -0.4, 0))
    d.parameter.expression = dia_expr
    return c


def polar_circle(ctx, sk, r_cm, theta_deg, r_seed_cm, dia_expr, r_expr, ang_expr):
    """A bound circle at (r_expr, ang_expr) polar. Position expressions are
    wrapped in abs() because distance dimensions are unsigned; the seed sits
    on the signed side so the solver keeps it there."""
    t = math.radians(theta_deg)
    w = (r_cm * math.cos(t), r_cm * math.sin(t), 0.0)
    return ctx.bound_circle(sk, w, r_seed_cm, dia_expr,
                            x_pos="abs( %s * cos( %s ) )" % (r_expr, ang_expr),
                            v_pos="abs( %s * sin( %s ) )" % (r_expr, ang_expr))


def profile_by_area(sk, want_cm2, tol=0.05):
    for p in sk.profiles:
        if abs(p.areaProperties().area - want_cm2) < tol * want_cm2:
            return p
    raise RuntimeError("no profile of area %.3f cm2 in %s" % (want_cm2, sk.name))


def circular_pattern_cut(ctx, feat, n_expr, watch, min_new_faces, name):
    """Circular pattern of one cut feature about the Z axis, validated by
    face-count delta (the kit's pattern_cut is rectangular only)."""
    healthy = (adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState,
               adsk.fusion.FeatureHealthStates.WarningFeatureHealthState)
    popts = adsk.fusion.PatternComputeOptions
    cp = ctx.root.features.circularPatternFeatures
    coll = adsk.core.ObjectCollection.create()
    coll.add(feat)
    before = ctx.faces_of(watch)
    reasons = []
    for mode in (popts.AdjustPatternCompute, popts.IdenticalPatternCompute):
        adsk.doEvents()
        inp = cp.createInput(coll, ctx.root.zConstructionAxis)
        inp.quantity = ctx.cbs(n_expr)
        inp.totalAngle = ctx.cbs("360 deg")
        inp.isSymmetric = False
        inp.patternComputeOption = mode  # pyright: ignore[reportAttributeAccessIssue]
        f = cp.add(inp)
        if f.healthState in healthy and ctx.faces_of(watch) - before >= min_new_faces:
            f.name = name
            return f
        reasons.append("%s hs=%s faces+%d" % (mode, f.healthState, ctx.faces_of(watch) - before))
        f.deleteMe()
    raise RuntimeError("circular pattern %s never validated: %s" % (name, " | ".join(reasons)))


def inside(body, x_mm, y_mm, z_mm):
    return body.pointContainment(adsk.core.Point3D.create(x_mm * MM, y_mm * MM, z_mm * MM)) \
        == adsk.fusion.PointContainment.PointInsidePointContainment


def probe(body, pts, want_inside, label):
    for (x, y, z) in pts:
        if inside(body, x, y, z) != want_inside:
            raise RuntimeError("%s: (%.1f, %.1f, %.1f) should be %s" % (
                label, x, y, z, "solid" if want_inside else "empty"))
    print("%s: %d probes %s" % (label, len(pts), "solid" if want_inside else "empty"))


# ---------------------------------------------------------------- build

def build_floor_and_wall(ctx):
    v = ctx.val
    sk = ctx.root.sketches.add(ctx.root.xYConstructionPlane)
    sk.name = "base_floor_sk"
    centred_circle(ctx, sk, v("drum_r"), "drum_d", 1)
    want = PI * v("drum_r") ** 2 * v("floor_t")
    f, base = ctx.checked_newbody(ctx.all_profiles(sk), "floor_t",
                                  lambda b: abs(b.volume - want) < 0.01 * want and b.boundingBox.maxPoint.z > 0.1,
                                  "floor")
    f.name = "base_floor"
    base.name = "base"
    print("base_floor: %.4f cm3 (want %.4f)" % (base.volume, want))

    floor_top = ctx.plane_at_z("floor_t", "floor_top")
    sk = ctx.root.sketches.add(floor_top)
    sk.name = "base_wall_sk"
    centred_circle(ctx, sk, v("drum_r"), "drum_d", 2)
    centred_circle(ctx, sk, v("cavity_r"), "2 * cavity_r", 3)
    ring = profile_by_area(sk, PI * (v("drum_r") ** 2 - v("cavity_r") ** 2))
    coll = adsk.core.ObjectCollection.create()
    coll.add(ring)
    v0 = base.volume
    want = PI * (v("drum_r") ** 2 - v("cavity_r") ** 2) * (v("split_z") - v("floor_t"))
    f = ctx.checked_join(coll, "split_z - floor_t", base,
                         lambda b: abs(b.volume - v0 - want) < 0.01 * want, "wall")
    f.name = "base_wall"
    check_delta("base_wall", v0, base.volume, want)
    return base, floor_top


def cut_channels(ctx, base):
    v = ctx.val
    sk = ctx.root.sketches.add(ctx.root.xYConstructionPlane)
    sk.name = "floor_channel_sk"
    r0, r1 = v("chan_r0"), v("drum_r") + 0.1
    ctx.bound_rect2(sk, ((r0 + r1) / 2, 0.0, 0.0), (r1 - r0) / 2, v("chan_w") / 2,
                    u_size="drum_r + 1 mm - chan_r0", v_size="chan_w",
                    u_pos=("( chan_r0 + drum_r + 1 mm ) / 2", "( drum_r + 1 mm - chan_r0 ) / 2"),
                    v_pos=("0 mm", "chan_w / 2"))
    v0 = base.volume
    f = ctx.blind_cut(ctx.all_profiles(sk), "chan_d", [base], "chan")
    f.name = "floor_channel"
    want = v("chan_w") * v("chan_d") * (v("drum_r") - r0)
    check_delta("floor_channel", v0, base.volume, -want, tol_rel=0.03)
    n = int(round(v("chan_n")))
    pat = circular_pattern_cut(ctx, f, "chan_n", [base], 3 * (n - 1), "floor_channel_pattern")
    check_delta("floor_channel_pattern", v0, base.volume, -want * n, tol_rel=0.03)
    return pat


def cut_intake(ctx, base):
    v = ctx.val
    sk = ctx.root.sketches.add(ctx.root.xYConstructionPlane)
    sk.name = "intake_holes_sk"
    n = int(round(v("chan_n")))
    for i in range(n):
        ang = "%d * 360 deg / chan_n" % i
        theta = i * 360.0 / n
        polar_circle(ctx, sk, v("intake_r1"), theta, v("intake_d") / 2, "intake_d", "intake_r1", ang)
        polar_circle(ctx, sk, v("intake_r2"), theta, v("intake_d") / 2, "intake_d", "intake_r2", ang)
        if i % 4 == 3:
            adsk.doEvents()
    v0 = base.volume
    faces0 = base.faces.count
    f = ctx.through_cut(ctx.all_profiles(sk), "floor_t * 2", [base])
    f.name = "intake_holes"
    want = 2 * n * PI * (v("intake_d") / 2) ** 2 * (v("floor_t") - v("chan_d"))
    check_delta("intake_holes", v0, base.volume, -want, tol_rel=0.05)
    if base.faces.count - faces0 < 2 * n:
        raise RuntimeError("intake_holes: only %d new faces" % (base.faces.count - faces0))


def build_pi_bosses(ctx, base, floor_top):
    v = ctx.val
    sk = ctx.root.sketches.add(floor_top)
    sk.name = "pi_boss_sk"
    hx, hy = v("pi_hole_px") / 2, v("pi_hole_py") / 2
    for sx, sy in PI_HOLES:
        ctx.bound_circle(sk, (sx * hx, sy * hy, v("floor_t")), v("pi_boss_d") / 2, "pi_boss_d",
                         x_pos="pi_hole_px / 2", v_pos="pi_hole_py / 2")
    v0 = base.volume
    want = 4 * PI * (v("pi_boss_d") / 2) ** 2 * v("pi_boss_h")
    f = ctx.checked_join(ctx.all_profiles(sk), "pi_boss_h", base,
                         lambda b: abs(b.volume - v0 - want) < 0.02 * want, "boss")
    f.name = "pi_boss"
    check_delta("pi_boss", v0, base.volume, want)

    boss_top = ctx.plane_at_z("floor_t + pi_boss_h", "boss_top")
    sk = ctx.root.sketches.add(boss_top)
    sk.name = "pi_insert_sk"
    for sx, sy in PI_HOLES:
        ctx.bound_circle(sk, (sx * hx, sy * hy, v("floor_t") + v("pi_boss_h")), v("pi_insert_hole") / 2,
                         "pi_insert_hole", x_pos="pi_hole_px / 2", v_pos="pi_hole_py / 2")
    v0 = base.volume
    f = ctx.blind_cut(ctx.all_profiles(sk), "pi_insert_h", [base], "insert", min_vol_cm3=0.01)
    f.name = "pi_insert"
    want = 4 * PI * (v("pi_insert_hole") / 2) ** 2 * v("pi_insert_h")
    check_delta("pi_insert", v0, base.volume, -want, tol_rel=0.03)


def cut_base_screws(ctx, base):
    """Countersunk M3 clearance holes from the underside at col_r on the
    column angles: a through-cut, then a 45 deg chamfer on each hole's edge
    at z 0, which is exactly a 90 deg countersink of csk_d. (The hole
    feature's countersink input failed with InternalValidationError:
    logicalSelection on 2026-10-22; cut + chamfer is kit-verifiable.)"""
    v = ctx.val
    sk = ctx.root.sketches.add(ctx.root.xYConstructionPlane)
    sk.name = "base_screw_sk"
    for ang in COL_ANGLES:
        polar_circle(ctx, sk, v("col_r"), ang, v("screw_clear_d") / 2, "screw_clear_d", "col_r", "%.1f deg" % ang)
        adsk.doEvents()
    r_hole, r_csk = v("screw_clear_d") / 2, v("csk_d") / 2
    h_cone = r_csk - r_hole                      # 90 deg countersink
    v0 = base.volume
    f = ctx.through_cut(ctx.all_profiles(sk), "floor_t * 2", [base], min_vol_cm3=0.05)
    f.name = "base_screw"
    want_hole = 4 * PI * r_hole ** 2 * v("floor_t")
    check_delta("base_screw", v0, base.volume, -want_hole)

    # The countersink: csk_d circles at z 0 extruded h_cone upward as a cut
    # with a 45 deg taper, so the cone narrows to screw_clear_d. No edge
    # references (a chamfer on the hole edges went fragile when chan_n
    # stepped, measured 2026-10-22). Direction and taper sign are probed
    # and validated by the frustum volume.
    sk = ctx.root.sketches.add(ctx.root.xYConstructionPlane)
    sk.name = "base_csk_sk"
    for ang in COL_ANGLES:
        polar_circle(ctx, sk, v("col_r"), ang, r_csk, "csk_d", "col_r", "%.1f deg" % ang)
        adsk.doEvents()
    want_cone = 4 * (PI * h_cone / 3 * (r_csk ** 2 + r_csk * r_hole + r_hole ** 2) - PI * r_hole ** 2 * h_cone)
    v1 = base.volume
    reasons = []
    for d in (ctx.dirs.PositiveExtentDirection, ctx.dirs.NegativeExtentDirection):
        for taper in ("-45 deg", "45 deg"):
            adsk.doEvents()
            inp = ctx.extrudes.createInput(ctx.all_profiles(sk), ctx.ops.CutFeatureOperation)
            ext = adsk.fusion.DistanceExtentDefinition.create(ctx.cbs("( csk_d - screw_clear_d ) / 2"))
            inp.setOneSideExtent(ext, d, ctx.cbs(taper))
            inp.participantBodies = [base]
            f = ctx.extrudes.add(inp)
            got = v1 - base.volume
            if abs(got - want_cone) < 0.02 * want_cone:
                f.name = "base_csk"
                check_delta("base_csk", v1, base.volume, -want_cone)
                return f
            reasons.append("%s/%s removed %.4f" % (d, taper, got))
            f.deleteMe()
    raise RuntimeError("base_csk: no direction/taper gave the frustum %.4f: %s" % (want_cone, reasons))


# ---------------------------------------------------------------- read-back

def read_back(ctx, base):
    v = ctx.val
    mm = lambda cm: cm * 10  # noqa: E731
    r0, r1, r2 = mm(v("chan_r0")), mm(v("intake_r1")), mm(v("intake_r2"))
    n = int(round(v("chan_n")))
    chan_pts, hole_pts, between = [], [], []
    for i in range(n):
        t = math.radians(i * 360.0 / n)
        chan_pts.append((65 * math.cos(t), 65 * math.sin(t), 1.0))
        hole_pts.append((r1 * math.cos(t), r1 * math.sin(t), 2.5))
        hole_pts.append((r2 * math.cos(t), r2 * math.sin(t), 2.5))
        t2 = math.radians((i + 0.5) * 360.0 / n)
        between.append((65 * math.cos(t2), 65 * math.sin(t2), 1.0))
    probe(base, chan_pts, False, "channels at r 65 z 1")
    probe(base, [(x, y, 2.5) for x, y, _ in chan_pts], True, "channel roofs at z 2.5")
    probe(base, between, True, "floor between channels")
    probe(base, hole_pts, False, "intake holes at z 2.5")
    hx, hy = mm(v("pi_hole_px")) / 2, mm(v("pi_hole_py")) / 2
    bz = mm(v("floor_t") + v("pi_boss_h"))
    probe(base, [(sx * hx, sy * hy, bz - 1) for sx, sy in PI_HOLES], False, "insert bores")
    probe(base, [(sx * hx + 2.5, sy * hy, bz - 1) for sx, sy in PI_HOLES], True, "boss walls")
    cr = mm(v("col_r"))
    screw = [(cr * math.cos(math.radians(a)), cr * math.sin(math.radians(a)), 1.5) for a in COL_ANGLES]
    probe(base, screw, False, "base screw holes at z 1.5 (signed coordinates)")
    # The column set is mirror-symmetric about both axes, so a sign slip
    # would land a hole on another hole's spot; the four distinct empty
    # probes above plus the four-hole volume already rule that out. This
    # checks the spots a 90 deg rotation would hit are solid.
    rotated = [(-y, x, z) for x, y, z in screw]
    probe(base, rotated, True, "screw positions rotated 90 deg are solid")
    probe(base, [(0, 0, 1.5), (79, 0, 20), (0, 79, 20)], True, "floor centre and wall")
    probe(base, [(0, 0, 10), (70, 0, 20)], False, "cavity")


def prove_live(ctx, name, stepped_expr, point_mm, restore_expr):
    """Step a parameter the signature probe cannot see, check that a point
    which was empty (a hole centre) becomes solid, and restore. The body is
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
        raise RuntimeError("prove_live %s: hole did not move when stepped to %s" % (name, stepped_expr))
    healthy_or_raise(ctx, "prove_live " + name)
    print("prove_live %s: stepped to %s, hole moved, restored" % (name, restore_expr))


def prove_symmetric_params(ctx):
    v = ctx.val
    hx, hy = v("pi_hole_px") * 5, v("pi_hole_py") * 5       # mm, half pitches
    bz = (v("floor_t") + v("pi_boss_h")) * 10 - 1
    prove_live(ctx, "intake_r1", "62 mm", (v("intake_r1") * 10, 0.0, 2.5), "58 mm")
    prove_live(ctx, "intake_r2", "72 mm", (v("intake_r2") * 10, 0.0, 2.5), "68 mm")
    prove_live(ctx, "pi_hole_px", "62 mm", (hx, hy, bz), "58 mm")
    prove_live(ctx, "pi_hole_py", "53 mm", (hx, hy, bz), "49 mm")


def render(ctx, tag):
    os.makedirs(RENDER_DIR, exist_ok=True)
    vp = ctx.app.activeViewport
    for name, orient in (("iso", adsk.core.ViewOrientations.IsoTopRightViewOrientation),
                         ("top", adsk.core.ViewOrientations.TopViewOrientation)):
        cam = vp.camera
        cam.viewOrientation = orient
        cam.isFitView = True
        vp.camera = cam
        adsk.doEvents()
        vp.saveAsImageFile(os.path.join(RENDER_DIR, "pi_drum_stage%s_%s.png" % (tag, name)), 1600, 1200)


def run(_context: str):
    app = adsk.core.Application.get()
    if not app.activeDocument.name.startswith(DOC_PREFIX):
        raise RuntimeError("wrong document %r: save a new design as %r first" % (app.activeDocument.name, DOC_PREFIX))
    ctx = BuildCtx(app)
    ensure_params(ctx)

    base, floor_top = build_floor_and_wall(ctx)
    cut_channels(ctx, base)
    cut_intake(ctx, base)
    build_pi_bosses(ctx, base, floor_top)
    cut_base_screws(ctx, base)
    ctx.plane_at_z("split_z", "split")
    adsk.doEvents()

    healthy_or_raise(ctx, "stage A")
    base = body_named(ctx, "base")
    read_back(ctx, base)
    prove_symmetric_params(ctx)
    base = body_named(ctx, "base")
    if ctx.root.bRepBodies.count != 1:
        raise RuntimeError("expected 1 body, found %d" % ctx.root.bRepBodies.count)
    bb = base.boundingBox
    print("base: %.1f x %.1f x %.1f mm, z %.1f..%.1f, %.4f cm3, %d faces" % (
        (bb.maxPoint.x - bb.minPoint.x) * 10, (bb.maxPoint.y - bb.minPoint.y) * 10,
        (bb.maxPoint.z - bb.minPoint.z) * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10,
        base.volume, base.faces.count))
    render(ctx, "A")
    print("done")
