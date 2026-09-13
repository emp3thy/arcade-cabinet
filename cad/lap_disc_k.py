"""Lap pad, D-014: the nested disc. Stage K -- two owner requests after stage J
(2026-09-13), in the document that holds stages A to J.

  ridge bevels  the two tyre ridges on the ring's outer wall (ridge_t proud,
                ridge_h tall, at ridge_lo_z and ridge_hi_z) each had a
                horizontal underside: an unsupported ledge when the ring
                prints open side up. An equal-distance chamfer of ridge_t on
                each ridge's bottom outer edge turns the underside into a 45
                deg slope; the ridge keeps its full width for the upper
                ridge_h - ridge_t. The tyre's grooves stay rectangular (a
                0.8 mm triangular void, cosmetic, inside the joint).
  inner bolts   four more M3 x 12 through the TPU ring's inner zone at
                in_rc / in_ang_1..4: counterbore + hole in the TPU ring,
                clearance through the sled floor, into base_boss_d x
                base_boss_h bosses standing on the sled floor with
                base_pilot pilots from below. Angles avoid the Brook (53..100
                deg at that radius), the LiPo tray (105..170) and stay under
                the stick and button bodies with the bosses at z 10.

The stage J ledge wedge was probed and found continuous over the port boss
(45 deg at x = 0, +-20, +-28), so no ceiling chamfer is needed there.

Oracles: Pappus volumes for the bevels (fraction of the circle from the
selected arc lengths), analytic volumes with inside-point probes for the
bosses, bolt lines read back with 0.02 cm epsilons.
"""
FH_ATTEMPT = 2
FH_OPTS = {
    "only_params": ["ridge_t", "in_rc", "in_ang_1"],
    "liveness_budget_s": 240,
    "max_bodies": 6,
}
INTERFERENCE_ALLOWED = []
CLEARANCES = []
EXPECT_DEAD = []  # namespace is reused across executes
from fusionhelper.buildkit import *

import adsk.core
import adsk.fusion
import math

PARAMS_K = (
    ("in_rc",     "62 mm",   "mm",  "inner TPU bolt radius; ring inner edge is at ring_id / 2"),
    ("in_ang_1",  "15 deg",  "deg", "inner bolt angle"),
    ("in_ang_2",  "195 deg", "deg", "inner bolt angle"),
    ("in_ang_3",  "255 deg", "deg", "inner bolt angle"),
    ("in_ang_4",  "315 deg", "deg", "inner bolt angle"),
)
NEEDED = ("floor_t", "ring_t", "ring_id", "ridge_t", "ridge_h", "ridge_od", "ridge_lo_z", "ridge_hi_z",
          "base_boss_d", "base_boss_h", "base_pilot", "base_pilot_depth", "base_bolt", "cb_d", "cb_depth")
N_IN = 4
PI = math.pi
EPS = 0.02


def ensure_params(ctx):
    for name in NEEDED:
        if ctx.up.itemByName(name) is None:
            raise RuntimeError("parameter %s missing: run stages A to J first" % name)
    for name, expr, unit, comment in PARAMS_K:
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


def join_named(ctx, profs, dist_expr, body_name, want_cm3, tol, kind, probe=None):
    inside = adsk.fusion.PointContainment.PointInsidePointContainment
    v0 = body_named(ctx, body_name).volume
    for d in ctx._try_dirs(kind):
        adsk.doEvents()
        if d is None:
            break
        inp = ctx.extrudes.createInput(profs, ctx.ops.JoinFeatureOperation)
        ctx._one_side(inp, dist_expr, d)
        inp.participantBodies = [body_named(ctx, body_name)]
        f = ctx.extrudes.add(inp)
        adsk.doEvents()
        body = body_named(ctx, body_name)
        added = body.volume - v0
        ok = abs(added - want_cm3) < tol * want_cm3
        if ok and probe is not None:
            ok = body.pointContainment(probe) == inside
        if ok:
            ctx._resolved[kind] = d
            return f, added
        f.deleteMe()
        adsk.doEvents()
    raise RuntimeError("%s: no direction added %.4f cm3 on the right side" % (kind, want_cm3))


def cut_named(ctx, profs, dist_expr, body_name, want_cm3, tol, kind):
    v0 = body_named(ctx, body_name).volume
    for d in ctx._try_dirs(kind):
        adsk.doEvents()
        if d is None:
            break
        inp = ctx.extrudes.createInput(profs, ctx.ops.CutFeatureOperation)
        ctx._one_side(inp, dist_expr, d)
        inp.participantBodies = [body_named(ctx, body_name)]
        f = ctx.extrudes.add(inp)
        adsk.doEvents()
        removed = v0 - body_named(ctx, body_name).volume
        if abs(removed - want_cm3) < tol * want_cm3:
            ctx._resolved[kind] = d
            return f, removed
        f.deleteMe()
        adsk.doEvents()
    raise RuntimeError("%s: no direction removed %.4f cm3" % (kind, want_cm3))


def polar_circles(ctx, sk, rc_expr, ang_prefix, n, rc, z, r_cm, dia_expr):
    for k in range(1, n + 1):
        theta = ctx.val("%s%d" % (ang_prefix, k))
        ctx.bound_circle(sk, (rc * math.cos(theta), rc * math.sin(theta), z), r_cm, dia_expr,
                         x_pos="abs(%s * cos(%s%d))" % (rc_expr, ang_prefix, k),
                         v_pos="abs(%s * sin(%s%d))" % (rc_expr, ang_prefix, k))
        adsk.doEvents()
    if not sk.isFullyConstrained:
        raise RuntimeError("%s sketch not fully constrained" % sk.name)


def ridge_bottom_edges(ctx, body, z_cm, r_cm):
    """Circle / arc edges of radius r_cm lying in the plane z = z_cm.
    Returns (collection, fraction of the full circle they cover)."""
    coll = adsk.core.ObjectCollection.create()
    length = 0.0
    for e in body.edges:  # fusionhelper: allow R11 — collection add, not a document mutation
        g = e.geometry
        circ = adsk.core.Circle3D.cast(g)
        arc = adsk.core.Arc3D.cast(g)
        if circ is not None:
            c, r = circ.center, circ.radius
        elif arc is not None:
            c, r = arc.center, arc.radius
        else:
            continue
        if abs(r - r_cm) > 0.003 or abs(c.z - z_cm) > 0.003 or math.hypot(c.x, c.y) > 0.003:
            continue
        coll.add(e)
        length += e.length
    return coll, length / (2 * PI * r_cm)


def ridge_bevel(ctx, name, z_param):
    chamfers = ctx.root.features.chamferFeatures
    if chamfers.itemByName(name) is not None:
        return
    v = ctx.val
    healthy = adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState
    inside = adsk.fusion.PointContainment.PointInsidePointContainment
    P = adsk.core.Point3D.create
    ring = body_named(ctx, "ring")
    R = v("ridge_od") / 2
    c = v("ridge_t")
    coll, frac = ridge_bottom_edges(ctx, ring, v(z_param), R)
    if coll.count == 0 or frac < 0.8:
        raise RuntimeError("%s: found %d edges covering %.2f of the circle" % (name, coll.count, frac))
    want = frac * 2 * PI * (R - c / 3) * 0.5 * c * c
    v0 = ring.volume
    cin = chamfers.createInput2()
    cin.chamferEdgeSets.addEqualDistanceChamferEdgeSet(coll, ctx.cbs("ridge_t"), False)
    cf = chamfers.add(cin)
    adsk.doEvents()
    ring = body_named(ctx, "ring")
    removed = v0 - ring.volume
    if cf.healthState != healthy or abs(removed - want) > 0.05 * want:
        raise RuntimeError("%s: health %s, removed %.4f cm3, wanted %.4f" % (name, cf.healthState, removed, want))
    cf.name = name
    # on the -x side (away from the port facet): ridge material gone just above the
    # old underside at the outer face, still present at the same height at the wall
    z = v(z_param)
    if ring.pointContainment(P(-(R - 0.2 * c), 0, z + 0.2 * c)) == inside:
        raise RuntimeError("%s: underside still square at the outer face" % name)
    if ring.pointContainment(P(-(R - 0.8 * c), 0, z + 0.2 * c)) == inside:
        raise RuntimeError("%s: bevel shallower than 45 deg" % name)
    if ring.pointContainment(P(-(R - 0.5 * c), 0, z + 0.7 * c)) != inside:
        raise RuntimeError("%s: bevel cut past 45 deg" % name)
    if ring.pointContainment(P(-(R - 0.2 * c), 0, z + v("ridge_h") - 0.2 * c)) != inside:
        raise RuntimeError("%s: ridge top lost its full width" % name)
    print("%s: -%.4f cm3 (want %.4f) over %d edge(s), %.0f%% of the circle; underside now 45 deg" % (
        name, removed, want, coll.count, frac * 100))


def run(_context: str):
    app = adsk.core.Application.get()
    if not app.activeDocument.name.startswith("Arcade Controller"):
        raise RuntimeError("wrong document " + app.activeDocument.name)
    ctx = BuildCtx(app)
    ensure_params(ctx)
    v = ctx.val
    P = adsk.core.Point3D.create
    inside = adsk.fusion.PointContainment.PointInsidePointContainment
    healthy = adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState

    # ---- tyre ridge bevels --------------------------------------------------------
    if v("ridge_t") >= v("ridge_h"):
        raise RuntimeError("ridge_t must be less than ridge_h for the bevel to leave a flat")
    ridge_bevel(ctx, "ridge_hi_bevel", "ridge_hi_z")
    ridge_bevel(ctx, "ridge_lo_bevel", "ridge_lo_z")
    adsk.doEvents()

    # ---- inner TPU bolts: sled bosses, pilots, sled holes, TPU holes + counterbores ---
    floor_plane = ctx.planes.itemByName("floor_plane")
    ring_plane = ctx.planes.itemByName("ring_plane")
    if floor_plane is None or ring_plane is None:
        raise RuntimeError("floor_plane or ring_plane missing")
    if v("in_rc") - v("cb_d") / 2 < v("ring_id") / 2 + 0.3:
        raise RuntimeError("inner bolts too close to the TPU ring's inner edge")
    if not feature_exists(ctx, "in_bosses"):
        sk = ctx.root.sketches.add(floor_plane)
        sk.name = "in_bosses"
        polar_circles(ctx, sk, "in_rc", "in_ang_", N_IN, v("in_rc"), v("floor_t"), v("base_boss_d") / 2, "base_boss_d")
        want = N_IN * PI * (v("base_boss_d") / 2) ** 2 * v("base_boss_h")
        t1 = v("in_ang_1")
        probe = P(v("in_rc") * math.cos(t1), v("in_rc") * math.sin(t1), v("floor_t") + v("base_boss_h") - EPS)
        f, added = join_named(ctx, ctx.all_profiles(sk), "base_boss_h", "sled", want, 0.02, "in_bosses", probe=probe)
        f.name = "in_bosses"
        print("inner bosses on the sled: +%.3f cm3 (want %.3f)" % (added, want))
    if not feature_exists(ctx, "in_pilots"):
        sk = ctx.root.sketches.add(ctx.root.xYConstructionPlane)
        sk.name = "in_pilots"
        polar_circles(ctx, sk, "in_rc", "in_ang_", N_IN, v("in_rc"), 0.0, v("base_pilot") / 2, "base_pilot")
        depth = v("floor_t") + v("base_pilot_depth")
        want = N_IN * PI * (v("base_pilot") / 2) ** 2 * depth
        f, removed = cut_named(ctx, ctx.all_profiles(sk), "floor_t + base_pilot_depth", "sled", want, 0.02, "in_pilots")
        f.name = "in_pilots"
        print("inner pilots: -%.4f cm3 (want %.4f), %.1f mm from the underside" % (removed, want, depth * 10))
    if not feature_exists(ctx, "in_tpu_holes"):
        sk = ctx.root.sketches.add(ring_plane)
        sk.name = "in_tpu_holes"
        polar_circles(ctx, sk, "in_rc", "in_ang_", N_IN, v("in_rc"), -v("ring_t"), v("base_bolt") / 2, "base_bolt")
        want = N_IN * PI * (v("base_bolt") / 2) ** 2 * v("ring_t")
        f, removed = cut_named(ctx, ctx.all_profiles(sk), "ring_t", "tpu_ring", want, 0.02, "in_tpu_holes")
        f.name = "in_tpu_holes"
        print("inner TPU holes: -%.4f cm3 (want %.4f)" % (removed, want))
    if not feature_exists(ctx, "in_tpu_cb"):
        sk = ctx.root.sketches.add(ring_plane)
        sk.name = "in_tpu_cb"
        polar_circles(ctx, sk, "in_rc", "in_ang_", N_IN, v("in_rc"), -v("ring_t"), v("cb_d") / 2, "cb_d")
        want = N_IN * PI * ((v("cb_d") / 2) ** 2 - (v("base_bolt") / 2) ** 2) * v("cb_depth")
        f, removed = cut_named(ctx, ctx.all_profiles(sk), "cb_depth", "tpu_ring", want, 0.02, "in_tpu_cb")
        f.name = "in_tpu_cb"
        print("inner TPU counterbores: -%.4f cm3 (want %.4f)" % (removed, want))
    adsk.doEvents()

    # ---- read-back ---------------------------------------------------------------
    sled, tpu = body_named(ctx, "sled"), body_named(ctx, "tpu_ring")
    for k in range(1, N_IN + 1):
        t = v("in_ang_%d" % k)
        x, y = v("in_rc") * math.cos(t), v("in_rc") * math.sin(t)
        if tpu.pointContainment(P(x, y, -v("ring_t") + EPS)) == inside:
            raise RuntimeError("inner bolt %d: counterbore blocked" % k)
        if sled.pointContainment(P(x, y, v("floor_t") / 2)) == inside:
            raise RuntimeError("inner bolt %d: floor hole blocked" % k)
        if sled.pointContainment(P(x, y, v("floor_t") + v("base_pilot_depth") - EPS)) == inside:
            raise RuntimeError("inner bolt %d: pilot blocked" % k)
        if sled.pointContainment(P(x, y, v("floor_t") + v("base_boss_h") - EPS)) != inside:
            raise RuntimeError("inner bolt %d: boss top missing" % k)
    print("inner bolt lines: 4 open through TPU and floor, blind in the sled bosses")

    tl = ctx.des.timeline
    bad = []
    for i in range(tl.count):
        it = tl.item(i)
        if it.isRolledBack:
            continue
        feat = adsk.fusion.Feature.cast(it.entity)
        if feat is not None and feat.healthState != healthy:
            bad.append(feat.name)
    if bad:
        raise RuntimeError("unhealthy timeline entries: %s" % bad)

    for name in ("ring", "sled", "plate", "tpu_ring", "tpu_tyre"):
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
