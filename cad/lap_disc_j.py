"""Lap pad, D-014: the nested disc. Stage J -- serviceable, printable assembly
(owner, 2026-09-13), in the document that holds stages A to I. Revised after
the first J (five executes, all rolled back): no lugs, no plate bosses.

  plate         plate_t 3.5 -> 5 mm so M3 heat-set inserts sit in the plate
                itself (no bosses hanging under a top-up print). The top face
                stays at plate_top_z; the plate grows downward, under_h drops
                by 1.5 mm.
  antenna       bracket moves from the front wall to ant_ang (60 deg,
                rear-right) so the 30 cm pigtail reaches the Brook with slack.
  hoops         hoop_gap off the wall so they belong to the floor at the split.
  split         SplitBody of the shell at floor_plane: walls, ledge, rim and
                port boss become "ring"; the floor slab and every lump on it
                are combined into "sled".
  ledge wedge   a 45 deg wedge under the ledge, all the way round except at
                the port boss: a chamfer of wedge_run on the concave edge
                where the cavity ceiling meets the wall (an inside-corner
                chamfer ADDS material). Makes the ring printable open side
                up, and carries the plate screws.
  plate screws  six 45 deg gussets (rib_*) from the wall up to the plate seat,
                one per screw; base_bolt holes down from plate_bot_z through them at
                screw_r / screw_ang_1..6, each with a cb_d spot face
                cb_top_z below the plate so the head bears on a flat; ins_d x
                ins_depth insert holes in the plate above them. M3 x 20 from
                inside the cavity; nothing on the top face.
  base bolts    six bosses on the ring's inner wall at base_ang_1..6 with
                base_pilot holes; base_bolt clearance through the sled floor;
                base_bolt + cb counterbore through the TPU ring. M3 x 12 from
                underneath; the same bolts clamp the TPU ring.
  tyre          stage D's tyre_round is replaced: the top outer edge keeps
                the tyre_r fillet, the bottom outer edge gets a 45 deg
                tyre_ch chamfer so the tyre prints flat without support.

Every join and cut asserts its analytic volume; the split's ring + sled
volumes sum to the shell's; joins whose two directions add the same volume
also probe a point that must be inside afterwards; bolt lines are read back
by point containment. All probes use 0.02 cm (0.2 mm) epsilons -- the first J
used 0.1 cm and landed a probe exactly on a hole's end face.
"""
FH_ATTEMPT = 2
FH_OPTS = {
    "only_params": ["ant_ang", "hoop_gap", "base_boss_d", "base_boss_h", "base_ang_1", "cb_d",
                    "wedge_run", "rib_tip", "rib_w", "screw_r", "screw_ang_1", "ins_d", "tyre_ch"],
    "liveness_budget_s": 300,
    "max_bodies": 6,
}
INTERFERENCE_ALLOWED = []
CLEARANCES = []
EXPECT_DEAD = []  # namespace is reused across executes
from fusionhelper.buildkit import *

import adsk.core
import adsk.fusion
import math

PARAMS_J = (
    ("ant_ang",         "60 deg",  "deg", "antenna bracket angle from +x; rear-right, near the Brook"),
    ("ant_rc",          "cavity_dia / 2 - ant_gap - ant_len / 2", "mm", "derived: bracket centre radius"),
    ("hoop_gap",        "0.4 mm",  "mm",  "hoop back off the wall so the hoop stays with the floor"),
    ("base_boss_d",     "8 mm",    "mm",  "ring boss for the base bolts"),
    ("base_boss_h",     "8 mm",    "mm",  "ring boss height above the floor line"),
    ("base_boss_in",    "0.5 mm",  "mm",  "boss overlap into the wall"),
    ("base_rc",         "cavity_dia / 2 - base_boss_d / 2 + base_boss_in", "mm", "derived: boss centre radius"),
    ("base_pilot",      "2.5 mm",  "mm",  "M3 thread-forming pilot in the ring boss"),
    ("base_pilot_depth", "7 mm",   "mm",  "pilot depth into the boss"),
    ("base_bolt",       "3.4 mm",  "mm",  "M3 clearance"),
    ("cb_d",            "7 mm",    "mm",  "counterbore / spot face for an M3 head"),
    ("cb_depth",        "3.5 mm",  "mm",  "TPU ring counterbore depth from its underside"),
    ("base_ang_1",      "55 deg",  "deg", "base bolt angle"),
    ("base_ang_2",      "115 deg", "deg", "base bolt angle"),
    ("base_ang_3",      "185 deg", "deg", "base bolt angle"),
    ("base_ang_4",      "235 deg", "deg", "base bolt angle"),
    ("base_ang_5",      "285 deg", "deg", "base bolt angle"),
    ("base_ang_6",      "345 deg", "deg", "base bolt angle"),
    ("wedge_run",       "cavity_dia / 2 - core_dia / 2 - 1 mm", "mm", "derived: 45 deg wedge under the ledge, 1 mm short of the ledge's inner edge"),
    ("rib_tip",         "104 mm",  "mm",  "screw gusset inner tip radius"),
    ("rib_w",           "10 mm",   "mm",  "screw gusset width along the wall"),
    ("rib_len",         "cavity_dia / 2 - rib_tip", "mm", "derived: gusset radial length = its height (45 deg)"),
    ("rib_ch",          "rib_len - 1 mm", "mm", "derived: 45 deg chamfer on the gusset block, 1 mm short of both faces"),
    ("rib_bot_z",       "plate_bot_z - rib_len", "mm", "derived: gusset block bottom at the wall"),
    ("screw_r",         "116 mm",  "mm",  "plate screw radius; 12 mm in from the gusset tip, 13 mm of gusset under the plate"),
    ("screw_ang_1",     "30 deg",  "deg", "plate screw angle; none in 76..104 (port boss) or 247..293 (art pocket)"),
    ("screw_ang_2",     "130 deg", "deg", "plate screw angle"),
    ("screw_ang_3",     "170 deg", "deg", "plate screw angle"),
    ("screw_ang_4",     "210 deg", "deg", "plate screw angle"),
    ("screw_ang_5",     "245 deg", "deg", "plate screw angle"),
    ("screw_ang_6",     "330 deg", "deg", "plate screw angle"),
    ("screw_hole_len",  "16 mm",   "mm",  "screw hole cut length down from the plate seat; exits the gusset slope"),
    ("cb_top_z",        "plate_bot_z - 9 mm", "mm", "derived: spot face ceiling; 9 mm of gusset above the head"),
    ("cb_cut_len",      "8 mm",    "mm",  "spot face cut length down from cb_top_z; exits the gusset slope"),
    ("ins_d",           "4 mm",    "mm",  "M3 heat-set insert hole in the plate"),
    ("ins_depth",       "4.2 mm",  "mm",  "insert hole depth from the plate underside; 0.8 mm skin left"),
    ("tyre_ch",         "10 mm",   "mm",  "tyre bottom outer edge chamfer, 45 deg"),
)
UPDATE = (("plate_t", "5 mm"),)
NEEDED = ("floor_t", "cavity_dia", "core_dia", "under_h", "plate_bot_z", "plate_top_z", "plate_t", "shell_h", "ring_t",
          "ant_gap", "ant_len", "ant_t", "ant_h", "ant_hole", "ant_hole_z", "hoop_d", "hoop_rc", "hoop_ang_1",
          "brook_cx", "brook_cy", "brook_pitch_x", "brook_pitch_y", "so_od", "tyre_od", "tyre_z0", "ridge_hi_z", "tyre_r",
          "port_cz", "port_plate_h", "boss_w", "disc_h")
DEAD_PARAMS = ("ant_cy", "ant_x")
N_BASE, N_SCREW, N_HOOP = 6, 6, 5
PI = math.pi
EPS = 0.02      # cm


def ensure_params(ctx):
    for name in NEEDED:
        if ctx.up.itemByName(name) is None:
            raise RuntimeError("parameter %s missing: run stages A to I first" % name)
    for name, expr, unit, comment in PARAMS_J:
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


def body_exists(ctx, name):
    for b in ctx.root.bRepBodies:
        if b.name == name:
            return True
    return False


def feature_exists(ctx, name):
    for n in (name, name + " (1)"):
        if ctx.extrudes.itemByName(n) is not None:
            return True
    return False


def delete_extrude(ctx, name):
    for n in (name, name + " (1)"):
        f = ctx.extrudes.itemByName(n)
        if f is not None:
            f.deleteMe()
            adsk.doEvents()
    sk = ctx.root.sketches.itemByName(name)
    if sk is not None:
        sk.deleteMe()
        adsk.doEvents()


def radial_plane_checked(ctx, ang_param, name, theta):
    probe = ctx.pt(10 * math.cos(theta), 10 * math.sin(theta), 1.0)
    for e in (ang_param, "-(%s)" % ang_param):
        pin = ctx.planes.createInput()
        pin.setByAngle(ctx.root.zConstructionAxis, ctx.cbs(e), ctx.root.xZConstructionPlane)
        pl = ctx.planes.add(pin)
        pl.name = name
        sk = ctx.root.sketches.add(pl)
        p = sk.modelToSketchSpace(probe)
        off = abs(p.z)
        sk.deleteMe()
        if off < 0.01:
            return pl
        pl.deleteMe()
        adsk.doEvents()
    raise RuntimeError("radial plane %s never contained the probe point" % name)


def plane_z(ctx, expr, name):
    pl = ctx.planes.itemByName(name)
    if pl is None:
        pl = ctx.plane_at_z(expr, name)
    return pl


def sym_join(ctx, profs, dist_expr, body_name, want_cm3, tol, label):
    v0 = body_named(ctx, body_name).volume
    inp = ctx.extrudes.createInput(profs, ctx.ops.JoinFeatureOperation)
    inp.setSymmetricExtent(ctx.cbs(dist_expr), True)
    inp.participantBodies = [body_named(ctx, body_name)]
    f = ctx.extrudes.add(inp)
    adsk.doEvents()
    added = body_named(ctx, body_name).volume - v0
    if abs(added - want_cm3) > tol * want_cm3:
        f.deleteMe()
        raise RuntimeError("%s: joined %.4f cm3, wanted %.4f" % (label, added, want_cm3))
    return f


def join_named(ctx, profs, dist_expr, body_name, want_cm3, tol, kind, probe=None):
    """One-sided join, target re-resolved by NAME before every read; probe
    is a point that must be inside afterwards (both directions can add the
    same volume when nothing sits on one side of the plane)."""
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
    """One-sided cut, target re-resolved by name; the direction whose removed
    volume matches want wins (a wrong direction removes a different amount)."""
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


def radial_rect(ctx, sk, theta, rc, r_half, z_c, z_half, r_size, r_pos, z_size, z_pos):
    ctx.U = (math.cos(theta), math.sin(theta), 0.0)
    ctx.V = (0.0, 0.0, 1.0)
    ctx.bound_rect2(sk, (rc * math.cos(theta), rc * math.sin(theta), z_c), r_half, z_half,
                    u_size=r_size, v_size=z_size, u_pos=(r_pos, "%s / 2" % r_size), v_pos=(z_pos, "%s / 2" % z_size))
    ctx.U = (1.0, 0.0, 0.0)
    ctx.V = (0.0, 1.0, 0.0)


def polar_circle(ctx, sk, rc_expr, ang_expr, rc, theta, z, r_cm, dia_expr):
    ctx.bound_circle(sk, (rc * math.cos(theta), rc * math.sin(theta), z), r_cm, dia_expr,
                     x_pos="abs(%s * cos(%s))" % (rc_expr, ang_expr),
                     v_pos="abs(%s * sin(%s))" % (rc_expr, ang_expr))


def polar_circles(ctx, sk, rc_expr, ang_prefix, n, rc, z, r_cm, dia_expr):
    for k in range(1, n + 1):
        polar_circle(ctx, sk, rc_expr, "%s%d" % (ang_prefix, k), rc, ctx.val("%s%d" % (ang_prefix, k)), z, r_cm, dia_expr)
        adsk.doEvents()
    if not sk.isFullyConstrained:
        raise RuntimeError("%s sketch not fully constrained" % sk.name)


def segment_area(r, d):
    if d >= r:
        return 0.0
    return r * r * math.acos(d / r) - d * math.sqrt(r * r - d * d)


def circle_edges(body, wants, tol=0.005):
    """Edges (full circles or arcs) matching (cx, cy, r, z); every want must
    match at least one edge (arcs may be split by other features)."""
    coll = adsk.core.ObjectCollection.create()
    hits = [0] * len(wants)
    seen = []
    for e in body.edges:  # fusionhelper: allow R11 — collection add, not a document mutation
        g = adsk.core.Circle3D.cast(e.geometry)
        if g is None:
            g = adsk.core.Arc3D.cast(e.geometry)
        if g is None:
            continue
        c, r = g.center, g.radius
        seen.append((round(c.x * 10, 1), round(c.y * 10, 1), round(r * 10, 2), round(c.z * 10, 2)))
        for i, (cx, cy, rr, z) in enumerate(wants):  # fusionhelper: allow R11 — collection add, not a document mutation
            if abs(c.x - cx) < tol and abs(c.y - cy) < tol and abs(r - rr) < tol and abs(c.z - z) < tol:
                coll.add(e)
                hits[i] += 1
    if any(h == 0 for h in hits):
        raise RuntimeError("edge match counts %s on %s; circles/arcs: %s" % (hits, body.name, sorted(set(seen))))
    return coll, hits


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
    floor_plane = ctx.planes.itemByName("floor_plane")
    if floor_plane is None:
        raise RuntimeError("floor_plane missing")
    split_done = body_exists(ctx, "ring") and body_exists(ctx, "sled")

    # ---- plate to 5 mm ------------------------------------------------------------
    for name, expr in UPDATE:
        p = ctx.up.itemByName(name)
        if p.expression.replace(" ", "") != expr.replace(" ", ""):
            p.expression = expr  # fusionhelper: allow R5 — no BRep handle held yet; bodies resolved by name below
            adsk.doEvents()
    plate = body_named(ctx, "plate")
    pb = plate.boundingBox
    if abs(pb.minPoint.z - v("plate_bot_z")) > EPS or abs(pb.maxPoint.z - (v("plate_top_z") + v("disc_h"))) > EPS:
        raise RuntimeError("plate z %.2f..%.2f, wanted %.2f..%.2f" % (pb.minPoint.z * 10, pb.maxPoint.z * 10, v("plate_bot_z") * 10, (v("plate_top_z") + v("disc_h")) * 10))
    if v("under_h") < v("port_cz") + v("port_plate_h") / 2 + 0.2:
        raise RuntimeError("port faceplate no longer clears the cavity ceiling")
    print("plate %.1f mm thick, z %.1f..%.1f; cavity ceiling at %.1f, faceplate top at %.1f" % (
        v("plate_t") * 10, pb.minPoint.z * 10, pb.maxPoint.z * 10, v("under_h") * 10, (v("port_cz") + v("port_plate_h") / 2) * 10))

    # ---- hoops off the wall --------------------------------------------------------
    hr = ctx.up.itemByName("hoop_rc")
    want_expr = "cavity_dia / 2 - hoop_d / 2 - hoop_gap"
    if hr.expression.replace(" ", "") != want_expr.replace(" ", ""):
        hr.expression = want_expr  # fusionhelper: allow R5 — bodies resolved by name below
        adsk.doEvents()
    if not split_done:
        shell = body_named(ctx, "shell")
        for k in range(1, N_HOOP + 1):
            t = v("hoop_ang_%d" % k)
            r_probe = v("cavity_dia") / 2 - v("hoop_gap") / 2
            if shell.pointContainment(P(r_probe * math.cos(t), r_probe * math.sin(t), v("floor_t") + 0.3)) == inside:
                raise RuntimeError("hoop_%d still touches the wall" % k)
        print("hoops: %.1f mm off the wall" % (v("hoop_gap") * 10))

    # ---- antenna bracket at ant_ang -----------------------------------------------
    if not split_done and not feature_exists(ctx, "ant_bracket"):
        shell = body_named(ctx, "shell")
        v_before = shell.volume
        old_plate = PI * (v("ant_hole") / 2) ** 2 * v("ant_t")
        old_bracket = v("ant_t") * v("ant_len") * v("ant_h") - old_plate
        delete_extrude(ctx, "antenna_hole")
        delete_extrude(ctx, "antenna_bracket")
        pl = ctx.planes.itemByName("antenna_plane")
        if pl is not None:
            pl.deleteMe()
            adsk.doEvents()
        shell = body_named(ctx, "shell")
        if abs((v_before - shell.volume) - old_bracket) > 0.03 * old_bracket:
            raise RuntimeError("old antenna bracket removal took %.3f cm3, wanted %.3f" % (v_before - shell.volume, old_bracket))
        theta = v("ant_ang")
        pl = radial_plane_checked(ctx, "ant_ang", "ant_plane", theta)
        sk = ctx.root.sketches.add(pl)
        sk.name = "ant_bracket"
        radial_rect(ctx, sk, theta, v("ant_rc"), v("ant_len") / 2, v("floor_t") + v("ant_h") / 2, v("ant_h") / 2,
                    "ant_len", "ant_rc", "ant_h", "floor_t + ant_h / 2")
        if not sk.isFullyConstrained:
            raise RuntimeError("ant_bracket sketch not fully constrained")
        want = v("ant_t") * v("ant_len") * v("ant_h")
        f = sym_join(ctx, ctx.all_profiles(sk), "ant_t", "shell", want, 0.02, "ant_bracket")
        f.name = "ant_bracket"
        sk = ctx.root.sketches.add(pl)
        sk.name = "ant_hole"
        ctx.U = (math.cos(theta), math.sin(theta), 0.0)
        ctx.V = (0.0, 0.0, 1.0)
        ctx.bound_circle(sk, (v("ant_rc") * math.cos(theta), v("ant_rc") * math.sin(theta), v("floor_t") + v("ant_hole_z")),
                         v("ant_hole") / 2, "ant_hole", x_pos="ant_rc", v_pos="floor_t + ant_hole_z")
        ctx.U = (1.0, 0.0, 0.0)
        ctx.V = (0.0, 1.0, 0.0)
        if not sk.isFullyConstrained:
            raise RuntimeError("ant_hole sketch not fully constrained")
        shell = body_named(ctx, "shell")
        v0 = shell.volume
        f = ctx.sym_cut(ctx.all_profiles(sk), "ant_t * 3", [shell], min_vol_cm3=0.5 * old_plate)
        f.name = "ant_hole"
        shell = body_named(ctx, "shell")
        if abs((v0 - shell.volume) - old_plate) > 0.03 * old_plate:
            raise RuntimeError("ant_hole removed %.4f cm3, wanted %.4f" % (v0 - shell.volume, old_plate))
        for name in DEAD_PARAMS:
            p = ctx.up.itemByName(name)
            if p is not None and not p.deleteMe():
                raise RuntimeError("parameter %s still referenced" % name)
            adsk.doEvents()
        sx = v("brook_cx") + v("brook_pitch_x") / 2
        sy = v("brook_cy") + v("brook_pitch_y") / 2
        d = math.hypot(v("ant_rc") * math.cos(theta) - sx, v("ant_rc") * math.sin(theta) - sy) - v("so_od") / 2 - v("ant_len") / 2
        if d < 0.3:
            raise RuntimeError("antenna bracket %.1f mm from the Brook standoff" % (d * 10))
        print("antenna bracket at %.0f deg, r %.1f mm: +%.3f cm3, hole -%.4f cm3, %.1f mm from the nearest standoff" % (
            math.degrees(theta), v("ant_rc") * 10, want, old_plate, d * 10))
    adsk.doEvents()

    # ---- split: shell -> ring + sled -------------------------------------------------
    if not split_done:
        shell = body_named(ctx, "shell")
        shell_v = shell.volume
        splits = ctx.root.features.splitBodyFeatures
        si = splits.createInput(shell, floor_plane, True)
        sf = splits.add(si)
        sf.name = "floor_split"
        adsk.doEvents()
        ring = slab = None
        lumps = []
        for b in ctx.root.bRepBodies:
            if b.name in ("plate", "tpu_ring", "tpu_tyre"):
                continue
            bb = b.boundingBox
            if bb.maxPoint.z > v("shell_h") - 0.01:
                ring = b
            elif bb.maxPoint.z <= v("floor_t") + 0.001:
                slab = b
            else:
                lumps.append(b)
        if ring is None or slab is None:
            raise RuntimeError("split did not yield ring and slab; bodies: %s" % [(b.name, round(b.boundingBox.maxPoint.z * 10, 1)) for b in ctx.root.bRepBodies])
        n_lumps = len(lumps)
        lump_v = sum(b.volume for b in lumps)
        ring.name = "ring"
        slab.name = "sled"
        adsk.doEvents()
        if n_lumps:
            tools = adsk.core.ObjectCollection.create()
            for b in lumps:  # fusionhelper: allow R11 — collection add, not a document mutation
                tools.add(b)
            combines = ctx.root.features.combineFeatures
            ci = combines.createInput(body_named(ctx, "sled"), tools)
            ci.operation = ctx.ops.JoinFeatureOperation  # pyright: ignore[reportAttributeAccessIssue]
            ci.isKeepToolBodies = False
            ci.isNewComponent = False
            cf = combines.add(ci)
            cf.name = "sled_combine"
            adsk.doEvents()
        ring = body_named(ctx, "ring")
        sled = body_named(ctx, "sled")
        if abs((ring.volume + sled.volume) - shell_v) > 0.01:
            raise RuntimeError("split lost volume: ring %.3f + sled %.3f != shell %.3f" % (ring.volume, sled.volume, shell_v))
        expect_lumps = 4 + 1 + N_HOOP + 1   # standoffs, tray+plinth, hoops, bracket
        if n_lumps != expect_lumps:
            raise RuntimeError("expected %d floor lumps, found %d" % (expect_lumps, n_lumps))
        print("split: ring %.2f cm3, sled %.2f cm3 (slab + %d lumps, %.2f cm3); bodies now %d" % (
            ring.volume, sled.volume, n_lumps, lump_v, ctx.root.bRepBodies.count))
    adsk.doEvents()

    # ---- ledge wedge: inside-corner chamfer on the ring ----------------------------
    chamfers = ctx.root.features.chamferFeatures
    if chamfers.itemByName("ledge_wedge") is None:
        ring = body_named(ctx, "ring")
        edges, hits = circle_edges(ring, [(0, 0, v("cavity_dia") / 2, v("under_h"))])
        run_cm = v("wedge_run")
        boss_half = math.asin((v("boss_w") / 2) / (v("cavity_dia") / 2))
        frac = 1.0 - (2 * boss_half) / (2 * PI)
        want = 0.5 * run_cm * run_cm * 2 * PI * (v("cavity_dia") / 2 - run_cm / 3) * frac
        v0 = ring.volume
        cin = chamfers.createInput2()
        cin.chamferEdgeSets.addEqualDistanceChamferEdgeSet(edges, ctx.cbs("wedge_run"), False)
        cf = chamfers.add(cin)
        adsk.doEvents()
        ring = body_named(ctx, "ring")
        added = ring.volume - v0
        if cf.healthState != healthy or abs(added - want) > 0.05 * want:
            raise RuntimeError("ledge_wedge: health %s, added %.3f cm3, wanted %.3f (%d edges)" % (cf.healthState, added, want, edges.count))
        cf.name = "ledge_wedge"
        # the wedge is run_cm tall at the wall and tapers to nothing at R_wall - run_cm
        t = v("screw_ang_1")
        r_probe = v("cavity_dia") / 2 - run_cm / 2
        z_slope = v("under_h") - run_cm / 2
        if ring.pointContainment(P(r_probe * math.cos(t), r_probe * math.sin(t), z_slope + 0.1)) != inside:
            raise RuntimeError("wedge missing above its slope at r %.0f" % (r_probe * 10))
        if ring.pointContainment(P(r_probe * math.cos(t), r_probe * math.sin(t), z_slope - 0.1)) == inside:
            raise RuntimeError("wedge thicker than 45 deg at r %.0f" % (r_probe * 10))
        print("ledge wedge: +%.2f cm3 (want %.2f) over %d edge(s), %.0f%% of the circle; %.1f mm tall at the wall" % (
            added, want, edges.count, frac * 100, run_cm * 10))
    adsk.doEvents()

    # ---- screw gussets: 45 deg ribs from the wall up to the plate seat ---------------
    rib_len = v("rib_len")
    rib_ch = v("rib_ch")
    wedge_tri = 0.5 * v("wedge_run") ** 2
    ledge_zone = (v("cavity_dia") / 2 - v("core_dia") / 2) * (v("plate_bot_z") - v("under_h"))
    block_want = (rib_len * rib_len - ledge_zone - wedge_tri) * v("rib_w")
    ch_want = 0.5 * rib_ch * rib_ch * v("rib_w")
    for k in range(1, N_SCREW + 1):
        name = "rib_%d" % k
        if chamfers.itemByName(name + "_ch") is not None:
            continue
        ang = "screw_ang_%d" % k
        theta = v(ang)
        pl = ctx.planes.itemByName(name + "_plane")
        if pl is None:
            pl = radial_plane_checked(ctx, ang, name + "_plane", theta)
        sk = ctx.root.sketches.add(pl)
        sk.name = name
        rc = v("cavity_dia") / 2 - rib_len / 2
        radial_rect(ctx, sk, theta, rc, rib_len / 2, v("rib_bot_z") + rib_len / 2, rib_len / 2,
                    "rib_len", "cavity_dia / 2 - rib_len / 2", "rib_len", "rib_bot_z + rib_len / 2")
        if not sk.isFullyConstrained:
            raise RuntimeError("%s sketch not fully constrained" % name)
        f = sym_join(ctx, ctx.all_profiles(sk), "rib_w", "ring", block_want, 0.04, name)
        f.name = name
        ring = body_named(ctx, "ring")
        coll = adsk.core.ObjectCollection.create()
        ux, uy = math.cos(theta), math.sin(theta)
        for e in ring.edges:  # fusionhelper: allow R11 — collection add, not a document mutation
            ln = adsk.core.Line3D.cast(e.geometry)
            if ln is None:
                continue
            a, b = e.startVertex.geometry, e.endVertex.geometry
            if abs(a.z - v("rib_bot_z")) > 0.005 or abs(b.z - v("rib_bot_z")) > 0.005:
                continue
            ra = a.x * ux + a.y * uy
            rb = b.x * ux + b.y * uy
            if abs(ra - v("rib_tip")) < 0.02 and abs(rb - v("rib_tip")) < 0.02:
                coll.add(e)
        if coll.count != 1:
            raise RuntimeError("%s: expected one bottom-inner edge, found %d" % (name, coll.count))
        v0 = ring.volume
        cin = chamfers.createInput2()
        cin.chamferEdgeSets.addEqualDistanceChamferEdgeSet(coll, ctx.cbs("rib_ch"), False)
        cf = chamfers.add(cin)
        adsk.doEvents()
        ring = body_named(ctx, "ring")
        if cf.healthState != healthy or abs((v0 - ring.volume) - ch_want) > 0.04 * ch_want:
            raise RuntimeError("%s chamfer: removed %.3f, wanted %.3f" % (name, v0 - ring.volume, ch_want))
        cf.name = name + "_ch"
        adsk.doEvents()
    print("screw gussets: 6 x (%.2f - %.2f) cm3, %.1f mm from the wall to the tip, slope at 45 deg" % (block_want, ch_want, rib_len * 10))

    # ---- plate screws: holes down through gussets, spot faces, plate inserts ---------
    z_slope_r = (v("plate_bot_z") - 0.1) - (v("screw_r") - v("rib_tip"))
    if not feature_exists(ctx, "screw_holes"):
        pl = ctx.planes.itemByName("plate_bot_plane")
        if pl is None:
            raise RuntimeError("plate_bot_plane missing")
        sk = ctx.root.sketches.add(pl)
        sk.name = "screw_holes"
        polar_circles(ctx, sk, "screw_r", "screw_ang_", N_SCREW, v("screw_r"), v("plate_bot_z"), v("base_bolt") / 2, "base_bolt")
        want = N_SCREW * PI * (v("base_bolt") / 2) ** 2 * (v("plate_bot_z") - z_slope_r)
        f, removed = cut_named(ctx, ctx.all_profiles(sk), "screw_hole_len", "ring", want, 0.03, "screw_holes")
        f.name = "screw_holes"
        print("plate screw holes: -%.4f cm3 (want %.4f), %.1f mm long" % (removed, want, (v("plate_bot_z") - z_slope_r) * 10))
    if not feature_exists(ctx, "screw_spots"):
        pl = plane_z(ctx, "cb_top_z", "cb_top_plane")
        sk = ctx.root.sketches.add(pl)
        sk.name = "screw_spots"
        polar_circles(ctx, sk, "screw_r", "screw_ang_", N_SCREW, v("screw_r"), v("cb_top_z"), v("cb_d") / 2, "cb_d")
        want = N_SCREW * PI * ((v("cb_d") / 2) ** 2 - (v("base_bolt") / 2) ** 2) * (v("cb_top_z") - z_slope_r)
        f, removed = cut_named(ctx, ctx.all_profiles(sk), "cb_cut_len", "ring", want, 0.04, "screw_spots")
        f.name = "screw_spots"
        print("screw spot faces: -%.4f cm3 (want %.4f), head seats at z %.1f, %.1f mm of ring above it" % (
            removed, want, v("cb_top_z") * 10, (v("plate_bot_z") - v("cb_top_z")) * 10))
    if not feature_exists(ctx, "insert_holes"):
        pl = ctx.planes.itemByName("plate_bot_plane")
        sk = ctx.root.sketches.add(pl)
        sk.name = "insert_holes"
        polar_circles(ctx, sk, "screw_r", "screw_ang_", N_SCREW, v("screw_r"), v("plate_bot_z"), v("ins_d") / 2, "ins_d")
        want = N_SCREW * PI * (v("ins_d") / 2) ** 2 * v("ins_depth")
        f, removed = cut_named(ctx, ctx.all_profiles(sk), "ins_depth", "plate", want, 0.02, "insert_holes")
        f.name = "insert_holes"
        print("plate insert holes: -%.4f cm3 (want %.4f), %.1f mm skin left" % (
            removed, want, (v("plate_top_z") - v("plate_bot_z") - v("ins_depth")) * 10))
    adsk.doEvents()

    # ---- base bosses on the ring + pilots --------------------------------------------
    if not feature_exists(ctx, "base_bosses"):
        sk = ctx.root.sketches.add(floor_plane)
        sk.name = "base_bosses"
        polar_circles(ctx, sk, "base_rc", "base_ang_", N_BASE, v("base_rc"), v("floor_t"), v("base_boss_d") / 2, "base_boss_d")
        r_b = v("base_boss_d") / 2
        want = N_BASE * (PI * r_b ** 2 - segment_area(r_b, v("cavity_dia") / 2 - v("base_rc"))) * v("base_boss_h")
        t1 = v("base_ang_1")
        probe = P(v("base_rc") * math.cos(t1), v("base_rc") * math.sin(t1), v("floor_t") + v("base_boss_h") - EPS)
        f, added = join_named(ctx, ctx.all_profiles(sk), "base_boss_h", "ring", want, 0.03, "base_bosses", probe=probe)
        f.name = "base_bosses"
        print("base bosses: +%.3f cm3 (want %.3f)" % (added, want))
    if not feature_exists(ctx, "base_pilots"):
        sk = ctx.root.sketches.add(floor_plane)
        sk.name = "base_pilots"
        polar_circles(ctx, sk, "base_rc", "base_ang_", N_BASE, v("base_rc"), v("floor_t"), v("base_pilot") / 2, "base_pilot")
        want = N_BASE * PI * (v("base_pilot") / 2) ** 2 * v("base_pilot_depth")
        f, removed = cut_named(ctx, ctx.all_profiles(sk), "base_pilot_depth", "ring", want, 0.02, "base_pilots")
        f.name = "base_pilots"
        print("base pilots: -%.4f cm3 (want %.4f)" % (removed, want))
    if not feature_exists(ctx, "sled_bolt_holes"):
        sk = ctx.root.sketches.add(ctx.root.xYConstructionPlane)
        sk.name = "sled_bolt_holes"
        polar_circles(ctx, sk, "base_rc", "base_ang_", N_BASE, v("base_rc"), 0.0, v("base_bolt") / 2, "base_bolt")
        want = N_BASE * PI * (v("base_bolt") / 2) ** 2 * v("floor_t")
        f, removed = cut_named(ctx, ctx.all_profiles(sk), "floor_t", "sled", want, 0.02, "sled_bolts")
        f.name = "sled_bolt_holes"
        print("sled bolt holes: -%.4f cm3 (want %.4f)" % (removed, want))
    ring_plane = ctx.planes.itemByName("ring_plane")
    if ring_plane is None:
        raise RuntimeError("ring_plane missing")
    if not feature_exists(ctx, "tpu_bolt_holes"):
        sk = ctx.root.sketches.add(ring_plane)
        sk.name = "tpu_bolt_holes"
        polar_circles(ctx, sk, "base_rc", "base_ang_", N_BASE, v("base_rc"), -v("ring_t"), v("base_bolt") / 2, "base_bolt")
        want = N_BASE * PI * (v("base_bolt") / 2) ** 2 * v("ring_t")
        f, removed = cut_named(ctx, ctx.all_profiles(sk), "ring_t", "tpu_ring", want, 0.02, "tpu_bolts")
        f.name = "tpu_bolt_holes"
        print("tpu bolt holes: -%.4f cm3 (want %.4f)" % (removed, want))
    if not feature_exists(ctx, "tpu_counterbores"):
        sk = ctx.root.sketches.add(ring_plane)
        sk.name = "tpu_counterbores"
        polar_circles(ctx, sk, "base_rc", "base_ang_", N_BASE, v("base_rc"), -v("ring_t"), v("cb_d") / 2, "cb_d")
        want = N_BASE * PI * ((v("cb_d") / 2) ** 2 - (v("base_bolt") / 2) ** 2) * v("cb_depth")
        f, removed = cut_named(ctx, ctx.all_profiles(sk), "cb_depth", "tpu_ring", want, 0.02, "tpu_cb")
        f.name = "tpu_counterbores"
        print("tpu counterbores: -%.4f cm3 (want %.4f)" % (removed, want))
    adsk.doEvents()

    # ---- tyre: fillet on top, chamfer below ---------------------------------------
    fillets = ctx.root.features.filletFeatures
    if chamfers.itemByName("tyre_bevel") is None:
        old = fillets.itemByName("tyre_round")
        tyre = body_named(ctx, "tpu_tyre")
        if old is not None:
            v0 = tyre.volume
            old.deleteMe()
            adsk.doEvents()
            tyre = body_named(ctx, "tpu_tyre")
            print("old tyre_round removed: +%.3f cm3 back" % (tyre.volume - v0))
        R, r_f, ch = v("tyre_od") / 2, v("tyre_r"), v("tyre_ch")
        edges, _ = circle_edges(tyre, [(0, 0, R, v("ridge_hi_z"))])
        want = 2 * PI * (R - 0.2234 * r_f) * r_f * r_f * (1 - PI / 4)
        v0 = tyre.volume
        fin = fillets.createInput()
        fin.edgeSetInputs.addConstantRadiusEdgeSet(edges, ctx.cbs("tyre_r"), True)
        ff = fillets.add(fin)
        adsk.doEvents()
        tyre = body_named(ctx, "tpu_tyre")
        if ff.healthState != healthy or abs((v0 - tyre.volume) - want) > 0.03 * want:
            raise RuntimeError("tyre_round (top): removed %.3f, wanted %.3f" % (v0 - tyre.volume, want))
        ff.name = "tyre_round"
        edges, _ = circle_edges(tyre, [(0, 0, R, v("tyre_z0"))])
        want = 0.5 * ch * ch * 2 * PI * (R - ch / 3)
        v0 = tyre.volume
        cin = chamfers.createInput2()
        cin.chamferEdgeSets.addEqualDistanceChamferEdgeSet(edges, ctx.cbs("tyre_ch"), False)
        cf = chamfers.add(cin)
        adsk.doEvents()
        tyre = body_named(ctx, "tpu_tyre")
        if cf.healthState != healthy or abs((v0 - tyre.volume) - want) > 0.03 * want:
            raise RuntimeError("tyre_bevel: removed %.3f, wanted %.3f" % (v0 - tyre.volume, want))
        cf.name = "tyre_bevel"
        print("tyre: top fillet r%.0f, bottom chamfer %.0f x 45 deg (-%.2f cm3); prints flat" % (r_f * 10, ch * 10, v0 - tyre.volume))
    adsk.doEvents()

    # ---- read-back: every bolt line open where it should be ---------------------------
    ring, sled, plate, tpu = body_named(ctx, "ring"), body_named(ctx, "sled"), body_named(ctx, "plate"), body_named(ctx, "tpu_ring")
    for k in range(1, N_BASE + 1):
        t = v("base_ang_%d" % k)
        x, y = v("base_rc") * math.cos(t), v("base_rc") * math.sin(t)
        if tpu.pointContainment(P(x, y, -v("ring_t") + EPS)) == inside:
            raise RuntimeError("base bolt %d: TPU counterbore blocked" % k)
        if sled.pointContainment(P(x, y, v("floor_t") / 2)) == inside:
            raise RuntimeError("base bolt %d: sled hole blocked" % k)
        if ring.pointContainment(P(x, y, v("floor_t") + v("base_pilot_depth") - EPS)) == inside:
            raise RuntimeError("base bolt %d: pilot blocked" % k)
        if ring.pointContainment(P(x, y, v("floor_t") + v("base_boss_h") - EPS)) != inside:
            raise RuntimeError("base bolt %d: boss top missing" % k)
    for k in range(1, N_SCREW + 1):
        t = v("screw_ang_%d" % k)
        x, y = v("screw_r") * math.cos(t), v("screw_r") * math.sin(t)
        if ring.pointContainment(P(x, y, v("cb_top_z") - EPS)) == inside:
            raise RuntimeError("plate screw %d: spot face blocked" % k)
        if ring.pointContainment(P(x, y, v("cb_top_z") + EPS)) == inside:
            raise RuntimeError("plate screw %d: screw hole blocked" % k)
        if ring.pointContainment(P(x, y, v("plate_bot_z") - EPS)) == inside:
            raise RuntimeError("plate screw %d: hole does not reach the plate seat" % k)
        if plate.pointContainment(P(x, y, v("plate_bot_z") + v("ins_depth") - EPS)) == inside:
            raise RuntimeError("plate screw %d: insert hole blocked" % k)
        if plate.pointContainment(P(x, y, v("plate_bot_z") + v("ins_depth") + EPS)) != inside:
            raise RuntimeError("plate screw %d: insert hole broke through" % k)
    print("bolt lines: 6 base bolts and 6 plate screws open and blind where intended")

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
