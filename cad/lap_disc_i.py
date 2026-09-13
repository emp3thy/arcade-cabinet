"""Lap pad, D-014: the nested disc. Stage I -- port board mount (OI-011), in
the document that holds stages A to H.

The port board (owner's photos and measurements, 2026-09-13) is Brook's
panel-mount board B-C16046: a black faceplate port_plate_w x port_plate_h x
port_plate_t carrying a USB Type-B socket and a 3.5 mm jack, a rear board
port_board_len deep behind it with a 5-pin cable to the Brook, and two M3
holes at diagonal corners port_hole_inset from the edges.

Mount: the faceplate sits flat against the INSIDE face of the port boss
(y = boss_y0), centred on x = 0, z = port_cz, and screws into the boss from
inside. The stage C window through the boss becomes the plug tunnel: port_w
x port_h shrink to 22 x 16 so the plug's overmould passes and the screw
holes land in solid boss (the stage E tyre window follows, to 23 x 17).
Four port_pilot holes port_pilot_depth deep are drilled into the boss's
inner face at the plate's four corners, so either diagonal fits.

Oracles: window faces read back at port_w x port_h; the four pilots remove
4 pi (port_pilot / 2)^2 port_pilot_depth; the plate outline sits inside
the boss face and the window inside the plate; the rear board's reach
(y = boss_y0 - port_board_len) clears the Brook standoffs.
"""
FH_ATTEMPT = 2
FH_OPTS = {
    "only_params": ["port_plate_w", "port_plate_h", "port_hole_inset", "port_pilot", "port_pilot_depth"],
    "liveness_budget_s": 120,
}
INTERFERENCE_ALLOWED = []
CLEARANCES = []
# The four pilots move symmetrically about the window centre when the plate
# size or hole inset changes: volume, bbox and centroid stay identical, so
# the signature probe reads all three as dead (attempt 1, measured). They are
# live: the script steps port_hole_inset and reads the pilot axes back.
EXPECT_DEAD = ["port_plate_w", "port_plate_h", "port_hole_inset"]
from fusionhelper.buildkit import *

import adsk.core
import adsk.fusion
import math

PARAMS_I = (
    ("port_plate_w",     "26.1 mm", "mm", "Brook panel board faceplate width (x)"),
    ("port_plate_h",     "31 mm",   "mm", "faceplate height (z)"),
    ("port_plate_t",     "1.5 mm",  "mm", "faceplate thickness"),
    ("port_board_len",   "28.3 mm", "mm", "rear board depth behind the faceplate"),
    ("port_hole_inset",  "3 mm",    "mm", "M3 hole centre from each plate edge (owner: 2 mm from the corner)"),
    ("port_pilot",       "2.5 mm",  "mm", "M3 thread-forming pilot in the boss"),
    ("port_pilot_depth", "6 mm",    "mm", "pilot depth into the boss_in 8 mm boss"),
    ("port_hole_dx",     "port_plate_w / 2 - port_hole_inset", "mm", "derived"),
    ("port_hole_dz",     "port_plate_h / 2 - port_hole_inset", "mm", "derived"),
)
UPDATE = (("port_w", "22 mm"), ("port_h", "16 mm"))
NEEDED = ("boss_y0", "boss_in", "port_cz", "port_w", "port_h", "floor_t", "under_h",
          "brook_cx", "brook_cy", "brook_pitch_y", "so_od", "boss_w")


def ensure_params(ctx):
    for name in NEEDED:
        if ctx.up.itemByName(name) is None:
            raise RuntimeError("parameter %s missing: run stages A to H first" % name)
    for name, expr, unit, comment in PARAMS_I:
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


def offset_plane_checked(ctx, base, expr, name, axis, want_cm):
    for e in (expr, "-(%s)" % expr):
        pin = ctx.planes.createInput()
        pin.setByOffset(base, ctx.cbs(e))
        pl = ctx.planes.add(pin)
        pl.name = name
        sk = ctx.root.sketches.add(pl)
        o = sk.sketchToModelSpace(ctx.pt(0, 0, 0))
        got = (o.x, o.y, o.z)[axis]
        if abs(got - want_cm) < 0.01:
            sk.deleteMe()
            return pl
        sk.deleteMe()
        pl.deleteMe()
        adsk.doEvents()
    raise RuntimeError("offset plane %s never landed at %.3f cm on axis %d" % (name, want_cm, axis))


def window_size(ctx, feature_name):
    """x and z extent of the port window from the cut feature's own faces."""
    f = None
    for n in (feature_name, feature_name + " (1)"):
        f = ctx.extrudes.itemByName(n)
        if f is not None:
            break
    if f is None:
        raise RuntimeError("%s missing" % feature_name)
    xs, zs = [], []
    for i in range(f.faces.count):
        bb = f.faces.item(i).boundingBox
        xs += [bb.minPoint.x, bb.maxPoint.x]
        zs += [bb.minPoint.z, bb.maxPoint.z]
    return (max(xs) - min(xs)) * 10, (max(zs) - min(zs)) * 10, (min(zs) + max(zs)) / 2 * 10


def run(_context: str):
    app = adsk.core.Application.get()
    if not app.activeDocument.name.startswith("Arcade Controller"):
        raise RuntimeError("wrong document " + app.activeDocument.name)
    ctx = BuildCtx(app)
    ensure_params(ctx)
    v = ctx.val

    # ---- window becomes the plug tunnel -----------------------------------------
    for name, expr in UPDATE:
        p = ctx.up.itemByName(name)
        if p.expression.replace(" ", "") != expr.replace(" ", ""):
            p.expression = expr  # fusionhelper: allow R5 — no BRep handle is held yet; bodies resolved by name below
            adsk.doEvents()
    shell = body_named(ctx, "shell")
    w, h, zc = window_size(ctx, "port_window")
    if abs(w - v("port_w") * 10) > 0.05 or abs(h - v("port_h") * 10) > 0.05 or abs(zc - v("port_cz") * 10) > 0.05:
        raise RuntimeError("port window reads %.2f x %.2f at z %.2f, wanted %.1f x %.1f at %.1f"
                           % (w, h, zc, v("port_w") * 10, v("port_h") * 10, v("port_cz") * 10))
    tw, th, _ = window_size(ctx, "tyre_window")
    print("port window %.1f x %.1f mm at z %.1f; tyre window %.1f x %.1f" % (w, h, zc, tw, th))

    # ---- layout checks --------------------------------------------------------
    hw, hh = v("port_plate_w") / 2, v("port_plate_h") / 2
    z_lo, z_hi = v("port_cz") - hh, v("port_cz") + hh
    if z_lo < v("floor_t") + 0.1 or z_hi > v("under_h") - 0.1:
        raise RuntimeError("faceplate z %.1f..%.1f mm does not sit on the boss face (%.1f..%.1f)"
                           % (z_lo * 10, z_hi * 10, v("floor_t") * 10, v("under_h") * 10))
    if hw > v("boss_w") / 2 - 0.1:
        raise RuntimeError("faceplate wider than the boss")
    if v("port_w") / 2 > hw or v("port_h") / 2 > hh:
        raise RuntimeError("window larger than the faceplate")
    dx, dz = v("port_hole_dx"), v("port_hole_dz")
    gap_z = dz - v("port_h") / 2 - v("port_pilot") / 2
    if gap_z < 0.15:
        raise RuntimeError("pilot holes only %.2f mm from the window" % (gap_z * 10))
    reach = v("boss_y0") - v("port_board_len")
    so_far = v("brook_cy") + v("brook_pitch_y") / 2 + v("so_od") / 2
    if reach < so_far + 0.1:
        raise RuntimeError("rear board reaches y=%.1f, Brook standoffs end at y=%.1f" % (reach * 10, so_far * 10))
    print("faceplate %.1f x %.1f at z %.1f..%.1f on boss face y=%.2f; pilots %.1f mm from the window; rear board to y=%.1f (standoffs end %.1f)"
          % (hw * 20, hh * 20, z_lo * 10, z_hi * 10, v("boss_y0") * 10, gap_z * 10, reach * 10, so_far * 10))

    # ---- four pilot holes into the boss's inner face -----------------------------
    if not feature_exists(ctx, "port_pilots"):
        pl = ctx.planes.itemByName("boss_in_plane")
        if pl is None:
            pl = offset_plane_checked(ctx, ctx.root.xZConstructionPlane, "boss_y0", "boss_in_plane", 1, v("boss_y0"))
        sk = ctx.root.sketches.add(pl)
        sk.name = "port_pilots"
        ctx.V = (0.0, 0.0, 1.0)
        for sx, sz in ((-1, 1), (1, 1), (-1, -1), (1, -1)):
            ctx.bound_circle(
                sk, (sx * dx, v("boss_y0"), v("port_cz") + sz * dz), v("port_pilot") / 2, "port_pilot",
                x_pos="port_hole_dx", v_pos="port_cz %s port_hole_dz" % ("+" if sz > 0 else "-"))
            adsk.doEvents()
        ctx.V = (0.0, 1.0, 0.0)
        if not sk.isFullyConstrained:
            raise RuntimeError("port_pilots sketch not fully constrained")
        want = 4 * math.pi * (v("port_pilot") / 2) ** 2 * v("port_pilot_depth")
        v0 = shell.volume
        f = ctx.blind_cut(ctx.all_profiles(sk), "port_pilot_depth", [shell], "pilots", min_vol_cm3=0.5 * want)
        f.name = "port_pilots"
        shell = body_named(ctx, "shell")
        removed = v0 - shell.volume
        if abs(removed - want) > 0.02 * want:
            raise RuntimeError("port_pilots removed %.4f cm3, wanted %.4f" % (removed, want))
        print("port pilots: -%.4f cm3 (want %.4f)" % (removed, want))
    adsk.doEvents()

    # ---- read-back: pilots open at the boss face, closed short of the facet -------
    P = adsk.core.Point3D.create
    inside = adsk.fusion.PointContainment.PointInsidePointContainment
    for sx, sz in ((-1, 1), (1, 1), (-1, -1), (1, -1)):
        x, z = sx * dx, v("port_cz") + sz * dz
        if shell.pointContainment(P(x, v("boss_y0") + 0.1, z)) == inside:
            raise RuntimeError("pilot at (%.1f, %.1f) not open" % (x * 10, z * 10))
        if shell.pointContainment(P(x, v("boss_y0") + v("port_pilot_depth") + 0.05, z)) != inside:
            raise RuntimeError("pilot at (%.1f, %.1f) broke through" % (x * 10, z * 10))
    print("pilots: open %.1f mm, solid beyond" % (v("port_pilot_depth") * 10))

    # ---- liveness read-back: pilot axes follow port_hole_inset -------------------
    def pilot_offsets():
        sh = body_named(ctx, "shell")
        xs = set()
        for face in sh.faces:
            cyl = adsk.core.Cylinder.cast(face.geometry)
            if cyl is None or abs(cyl.radius - v("port_pilot") / 2) > 0.005:
                continue
            o = cyl.origin
            if abs(o.y - v("boss_y0")) > v("port_pilot_depth") + 0.1 or o.y < v("boss_y0") - 0.1:
                continue
            xs.add(round(abs(o.x) * 10, 2))
        return sorted(xs)

    d0 = pilot_offsets()
    if d0 != [round(v("port_hole_dx") * 10, 2)]:
        raise RuntimeError("pilot x offsets read %s, wanted %.2f" % (d0, v("port_hole_dx") * 10))
    ctx.up.itemByName("port_hole_inset").expression = "4 mm"  # fusionhelper: allow R5 — pilot_offsets re-resolves the shell by name; shell re-resolved below
    adsk.doEvents()
    d1 = pilot_offsets()
    ctx.up.itemByName("port_hole_inset").expression = "3 mm"  # fusionhelper: allow R5 — pilot_offsets re-resolves the shell by name; shell re-resolved below
    adsk.doEvents()
    d2 = pilot_offsets()
    shell = body_named(ctx, "shell")
    if d1 != [round((v("port_plate_w") / 2 - 0.4) * 10, 2)] or d2 != d0:
        raise RuntimeError("port_hole_inset not live: %s -> %s -> %s" % (d0, d1, d2))
    print("port_hole_inset live: pilot |x| %.2f -> %.2f -> %.2f mm" % (d0[0], d1[0], d2[0]))

    tl = ctx.des.timeline
    bad = []
    for i in range(tl.count):
        it = tl.item(i)
        if it.isRolledBack:
            continue
        feat = adsk.fusion.Feature.cast(it.entity)
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
