"""Lap pad, D-014: the nested disc. Stage L -- the port board's headroom
(2026-09-13), in the document that holds stages A to K.

Stage J's ledge wedge (an inside-corner chamfer of wedge_run on the cavity
ceiling / wall edge) runs the whole way round, so over the port boss it
swept through the two upper pilot holes and refilled them, and it also
takes the top 4.4 mm of the board's envelope: at the boss face the wedge's
underside sits at z 34.5 to 35.3 across the board width, while the board's
faceplate reaches port_cz + port_plate_h / 2 = 39.7.

  port_relief   an axis-aligned box cut out of the wedge over the board:
                2 * relief_hw wide, relief_depth inboard of the boss face,
                from relief_h below the ceiling up to the ceiling. Nothing
                of the wedge is left above the board there.
  port_gable    an inside-corner chamfer of relief_ch on the edge the cut
                leaves at (boss_y0, under_h): a 45 deg fill hanging from
                the ceiling down the boss face, bottom at under_h -
                relief_ch, 0.8 mm clear of the board. The ceiling strip
                between the gable and the untouched wedge is relief_depth -
                relief_ch = 3 mm, bridged between two supports.
  port_pilots_k the four pilots re-cut after the wedge; only the upper two
                have anything to remove.

Print orientation is unchanged: ring open side up, and every new
downward-facing surface is either a 45 deg slope or a 3 mm bridge.

Oracles: numeric integration of the wedge prism for the cut, Pappus for the
gable, analytic cylinders for the pilots, then the board envelope and all
four bolt lines read back with 0.02 cm epsilons.
"""
FH_ATTEMPT = 1
FH_OPTS = {
    "only_params": ["relief_depth", "relief_ch"],
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

PARAMS_L = (
    ("relief_hw",    "14 mm", "mm", "half width of the port board relief; the board is port_plate_w wide"),
    ("relief_depth", "6 mm",  "mm", "how far inboard of the boss face the relief cuts the ledge wedge"),
    ("relief_h",     "11 mm", "mm", "relief cut height, measured down from the cavity ceiling"),
    ("relief_cy",    "boss_y0 - relief_depth / 2", "mm", "derived: relief centre in y"),
    ("relief_ch",    "under_h - port_cz - port_plate_h / 2 - 0.8 mm", "mm",
     "derived: 45 deg gable from the ceiling down the boss face, 0.8 mm clear of the board top"),
)
NEEDED = ("under_h", "wedge_run", "cavity_dia", "boss_y0", "boss_w", "port_cz", "port_plate_h", "port_plate_w",
          "port_board_len", "port_hole_dx", "port_hole_dz", "port_pilot", "port_pilot_depth", "floor_t")
PI = math.pi
EPS = 0.02
NGRID = 80


def ensure_params(ctx):
    for name in NEEDED:
        if ctx.up.itemByName(name) is None:
            raise RuntimeError("parameter %s missing: run stages A to K first" % name)
    for name, expr, unit, comment in PARAMS_L:
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


def wedge_top(v, r_cm):
    """Height of wedge material between its 45 deg underside and the ceiling,
    at radius r_cm. Zero inboard of where the chamfer dies out."""
    h = v("wedge_run") - v("cavity_dia") / 2 + r_cm
    return max(0.0, min(h, v("wedge_run")))


def relief_volume(v):
    """Numeric integral of the wedge prism inside the relief box."""
    hw = v("relief_hw")
    y0 = v("boss_y0") - v("relief_depth")
    y1 = v("boss_y0")
    dx = 2 * hw / NGRID
    dy = (y1 - y0) / NGRID
    total = 0.0
    for i in range(NGRID):
        x = -hw + (i + 0.5) * dx
        for j in range(NGRID):
            y = y0 + (j + 0.5) * dy
            total += min(wedge_top(v, math.hypot(x, y)), v("relief_h"))
    return total * dx * dy


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

    board_top = v("port_cz") + v("port_plate_h") / 2
    board_hw = v("port_plate_w") / 2
    # the relief must be deep enough that the untouched wedge clears the board
    r_corner = math.hypot(board_hw, v("boss_y0") - v("relief_depth"))
    if v("under_h") - wedge_top(v, r_corner) < board_top + 0.05:
        raise RuntimeError("relief_depth too small: wedge is at z %.1f, board top %.1f"
                           % ((v("under_h") - wedge_top(v, r_corner)) * 10, board_top * 10))
    if v("relief_h") < wedge_top(v, math.hypot(v("relief_hw"), v("boss_y0"))) + 0.05:
        raise RuntimeError("relief_h too small to reach under the wedge at the relief corner")
    if not 0 < v("relief_ch") < v("relief_depth"):
        raise RuntimeError("relief_ch %.2f must sit inside relief_depth" % (v("relief_ch") * 10))
    if v("relief_hw") < board_hw + 0.05:
        raise RuntimeError("relief narrower than the board")

    # ---- relief: cut the wedge away over the board --------------------------------
    if not feature_exists(ctx, "port_relief"):
        pl = ctx.planes.itemByName("relief_plane")
        if pl is None:
            pl = ctx.plane_at_z("under_h - relief_h", "relief_plane")
        sk = ctx.root.sketches.add(pl)
        sk.name = "port_relief"
        ctx.bound_rect2(sk, (0.0, v("relief_cy"), v("under_h") - v("relief_h")),
                        v("relief_hw"), v("relief_depth") / 2,
                        u_size="2 * relief_hw", v_size="relief_depth",
                        u_pos=("0 mm", "relief_hw"), v_pos=("relief_cy", "relief_depth / 2"))
        if not sk.isFullyConstrained:
            raise RuntimeError("port_relief sketch not fully constrained")
        want = relief_volume(v)
        f, removed = cut_named(ctx, ctx.all_profiles(sk), "relief_h", "ring", want, 0.03, "port_relief")
        f.name = "port_relief"
        print("port relief: -%.3f cm3 (want %.3f), %.1f x %.1f mm up to the ceiling" % (
            removed, want, 2 * v("relief_hw") * 10, v("relief_depth") * 10))
    adsk.doEvents()

    # ---- gable: 45 deg fill from the ceiling down the boss face ----------------------
    chamfers = ctx.root.features.chamferFeatures
    if chamfers.itemByName("port_gable") is None:
        ring = body_named(ctx, "ring")
        coll = adsk.core.ObjectCollection.create()
        for e in ring.edges:  # fusionhelper: allow R11 — collection add, not a document mutation
            if adsk.core.Line3D.cast(e.geometry) is None:
                continue
            a, b = e.startVertex.geometry, e.endVertex.geometry
            if abs(a.z - v("under_h")) < 0.005 and abs(b.z - v("under_h")) < 0.005 \
                    and abs(a.y - v("boss_y0")) < 0.005 and abs(b.y - v("boss_y0")) < 0.005:
                coll.add(e)
        if coll.count != 1:
            raise RuntimeError("gable edge: expected 1 at the boss face, found %d" % coll.count)
        gable_edge = adsk.fusion.BRepEdge.cast(coll.item(0))
        if gable_edge is None or abs(gable_edge.length - 2 * v("relief_hw")) > 0.02:
            raise RuntimeError("gable edge is %.1f mm long, wanted %.1f"
                               % (-1.0 if gable_edge is None else gable_edge.length * 10,
                                  2 * v("relief_hw") * 10))
        want = 0.5 * v("relief_ch") ** 2 * 2 * v("relief_hw")
        v0 = ring.volume
        cin = chamfers.createInput2()
        cin.chamferEdgeSets.addEqualDistanceChamferEdgeSet(coll, ctx.cbs("relief_ch"), False)
        cf = chamfers.add(cin)
        adsk.doEvents()
        ring = body_named(ctx, "ring")
        added = ring.volume - v0
        if cf.healthState != healthy or abs(added - want) > 0.05 * want:
            raise RuntimeError("port_gable: health %s, added %.4f cm3, wanted %.4f"
                               % (cf.healthState, added, want))
        cf.name = "port_gable"
        c = v("relief_ch")
        yb, zc = v("boss_y0"), v("under_h")
        if ring.pointContainment(P(0, yb - c / 2, zc - c / 2 + 0.05)) != inside:
            raise RuntimeError("gable fill missing")
        if ring.pointContainment(P(0, yb - c / 2, zc - c / 2 - 0.05)) == inside:
            raise RuntimeError("gable steeper than 45 deg")
        print("port gable: +%.4f cm3 (want %.4f), %.1f mm at 45 deg, bottom z %.1f" % (
            added, want, c * 10, (zc - c) * 10))
    adsk.doEvents()

    # ---- pilots re-cut after the wedge ----------------------------------------------
    if not feature_exists(ctx, "port_pilots_k"):
        pl = ctx.planes.itemByName("boss_in_plane")
        if pl is None:
            raise RuntimeError("boss_in_plane missing")
        sk = ctx.root.sketches.add(pl)
        sk.name = "port_pilots_k"
        for sx in (-1, 1):
            for sz in (-1, 1):
                ctx.bound_circle(
                    sk, (sx * v("port_hole_dx"), v("boss_y0"), v("port_cz") + sz * v("port_hole_dz")),
                    v("port_pilot") / 2, "port_pilot",
                    x_pos="port_hole_dx",
                    v_pos="abs(port_cz %s port_hole_dz)" % ("+" if sz > 0 else "-"))
                adsk.doEvents()
        if not sk.isFullyConstrained:
            raise RuntimeError("port_pilots_k sketch not fully constrained")
        want = 2 * PI * (v("port_pilot") / 2) ** 2 * v("port_pilot_depth")
        f, removed = cut_named(ctx, ctx.all_profiles(sk), "port_pilot_depth", "ring", want, 0.03, "port_pilots_k")
        f.name = "port_pilots_k"
        print("pilots re-cut: -%.4f cm3 (want %.4f, the two upper holes)" % (removed, want))
    adsk.doEvents()

    # ---- read-back: four open pilots, board envelope clear ---------------------------
    ring = body_named(ctx, "ring")
    for sx in (-1, 1):
        for sz in (-1, 1):
            x = sx * v("port_hole_dx")
            z = v("port_cz") + sz * v("port_hole_dz")
            if ring.pointContainment(P(x, v("boss_y0") + v("port_pilot_depth") - EPS, z)) == inside:
                raise RuntimeError("pilot x %.1f z %.1f still blocked" % (x * 10, z * 10))
            if ring.pointContainment(P(x, v("boss_y0") + v("port_pilot_depth") + 0.05, z)) != inside:
                raise RuntimeError("pilot x %.1f z %.1f runs past its depth" % (x * 10, z * 10))
    print("all four pilots open %.1f mm deep and blind beyond" % (v("port_pilot_depth") * 10))

    worst = 1.0e9
    for i in range(25):
        x = -board_hw + 2 * board_hw * i / 24.0
        for j in range(31):
            y = v("boss_y0") - v("port_board_len") * j / 30.0
            for z in (board_top, v("port_cz") - v("port_plate_h") / 2):
                if ring.pointContainment(P(x, y, z)) == inside:
                    raise RuntimeError("board envelope hits the ring at (%.1f, %.1f, %.1f)"
                                       % (x * 10, y * 10, z * 10))
            r = math.hypot(x, y)
            gap = v("under_h") - wedge_top(v, r) - board_top
            if y > v("boss_y0") - v("relief_depth"):
                gap = v("under_h") - v("relief_ch") - board_top
            worst = min(worst, gap)
    print("board envelope clear; tightest headroom %.2f mm" % (worst * 10))

    ceiling_strip = v("relief_depth") - v("relief_ch")
    print("flat ceiling left over the board: %.1f mm, bridged between the gable and the wedge" % (ceiling_strip * 10))

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
