"""Pi console drum, D-021. Stage E -- print fixes, overhang audit, exports
and renders (plan task 7), in the document that holds stages A to D.

Two print-orientation faults found while writing the audit (the cup prints
inverted, lid on the bed; the base prints as modelled):
  col_roof_n   the webs and columns hung from the cup wall with flat tops
               at web_z1, which print as 90 deg undersides. web_z1 is raised
               40 -> 46 and everything above the 45 deg plane
               z = roof_z + (r - col_r), between roof_r0 and cavity_r, is cut
               away: the top of each web and column becomes a 45 deg roof
               rising toward the wall (36 at the column's inner edge, 40 on
               its axis, 44.2 at the wall).
  pad_n_foot   each socket pad's block started at pad_z0 - 1 = 5, two mm above
               the floor, a cantilevered underside; a foot fills z floor_t..5
               under each block.
Then:
  specks       inlay pieces under SPECK_CM3 (the silhouettes' four 1.2-1.4
               mm3 bits each) are joined back into the cup: no pits, no
               speck bodies to colour in the slicer.
  audit        every face of every body, normal sampled at its parametric
               centre, flipped for the inverted cup; a face steeper than 45
               deg overhang is printed with a class: bed, ledge (<= 1.5 mm),
               bridge (<= 20 mm between walls), rim ring (the vent groove
               floor), pocket (the art fill rule), small hole, or
               UNCLASSIFIED, which raises after the full list is printed.
  exports      cad/exports/pi_drum.step (all bodies) and pi_drum.3mf
  renders      explicit cameras: iso, front, left, right, top, base from
               above (cup hidden), cup from below (base hidden)

Oracles: web_z1's step adds the computed web and column volume; each roof
cut removes the numerically integrated volume above its plane; each foot
adds its block less the wall overlap (stage B's integral); the specks'
volumes move from the inlays to the cup exactly.
"""
FH_ATTEMPT = 1
FH_OPTS = {
    "only_params": ["roof_z", "roof_r0"],
    "liveness_budget_s": 600,
    "max_bodies": 20,
    "force_liveness": True,
}
INTERFERENCE_ALLOWED = []
CLEARANCES = []
EXPECT_DEAD = []
from fusionhelper.buildkit import *

import adsk.core
import adsk.fusion
import math
import os

DOC_PREFIX = "arcade unit v1"
ROOT = r"C:/Users/gethi/sources/arcade-cabinet/.claude/worktrees/pi-drum/cad"
RENDER_DIR = ROOT + "/renders"
EXPORT_DIR = ROOT + "/exports"
PI = math.pi
MM = 0.1
TOL_MM = 0.05
VOL_TOL = 1e-6
SPECK_CM3 = 0.01
OVERHANG_NZ = -0.7075          # print-orientation normal z below this is steeper than 45 deg
LEDGE_MM, BRIDGE_MM = 1.5, 20.0

NEEDED = ("drum_r", "cavity_r", "floor_t", "split_z", "drum_h", "lid_t", "col_r", "col_d", "web_w", "web_z1",
          "pad_r", "pad_w", "pad_back_t", "pad_z0", "art_pocket_d", "vent_z0", "vent_z1", "inlay_d")
PARAMS = (
    ("roof_z",  "40 mm", "mm", "45 deg roof plane height on the column axis; rises 1:1 toward the wall"),
    ("roof_r0", "col_r - col_d / 2 - 1 mm", "mm", "derived: roof cut starts 1 mm inside the column's inner edge"),
)
WEB_Z1_NEW = "46 mm"
WEB_Z1_OLD = "40 mm"
COL_ANGLES = (("1", 20.0), ("2", 160.0), ("3", -160.0), ("4", -20.0))
PADS = (("rj45", 45.0), ("usbc", 75.0), ("hdmi", 105.0), ("usba", 135.0))


# ---------------------------------------------------------------- helpers

def ensure_params(ctx):
    for name in NEEDED:
        if ctx.up.itemByName(name) is None:
            raise RuntimeError("parameter %s missing: run stages A to D first" % name)
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


def group(ctx, name):
    return [b for b in ctx.root.bRepBodies if b.name == name or b.name.startswith(name + " (")]


def plane_named(ctx, name):
    for i in range(ctx.planes.count):
        if ctx.planes.item(i).name == name:
            return ctx.planes.item(i)
    raise RuntimeError("no construction plane named %s" % name)


def radial_rect(ctx, sk, theta, r_c, z_c, r_half, z_half, r_size, r_pos, z_size, z_pos):
    ctx.U = (math.cos(theta), math.sin(theta), 0.0)
    ctx.V = (0.0, 0.0, 1.0)
    try:
        ctx.bound_rect2(sk, (r_c * math.cos(theta), r_c * math.sin(theta), z_c), r_half, z_half,
                        u_size=r_size, v_size=z_size,
                        u_pos=(r_pos, "( %s ) / 2" % r_size), v_pos=(z_pos, "( %s ) / 2" % z_size))
    finally:
        ctx.U = (1.0, 0.0, 0.0)
        ctx.V = (0.0, 1.0, 0.0)


def landed_rz(sk, theta):
    n = (math.cos(theta), math.sin(theta))
    rs, zs = [], []
    for i in range(sk.sketchCurves.sketchLines.count):
        ln = sk.sketchCurves.sketchLines.item(i)
        for p in (ln.startSketchPoint.geometry, ln.endSketchPoint.geometry):
            m = sk.sketchToModelSpace(p)
            rs.append((m.x * n[0] + m.y * n[1]) * 10)
            zs.append(m.z * 10)
    return min(rs), max(rs), min(zs), max(zs)


def assert_landed(sk, theta, want, label):
    got = landed_rz(sk, theta)
    if any(abs(g - w) > TOL_MM for g, w in zip(got, want)):
        raise RuntimeError("%s: landed r %.2f..%.2f z %.2f..%.2f, wanted r %.2f..%.2f z %.2f..%.2f" % ((label,) + got + want))
    print("%s: at r %.2f..%.2f z %.2f..%.2f" % ((label,) + got))


def sym_cut_checked(ctx, sk, width_expr, body, want, label, tol_rel=0.02, min_vol=0.01):
    v0 = body.volume
    f = ctx.sym_cut(ctx.all_profiles(sk), width_expr, [body], min_vol_cm3=min_vol)
    f.name = label
    check_delta(label, v0, body.volume, -want, tol_rel=tol_rel)
    return f


def sym_join_checked(ctx, sk, width_expr, body, want, label, tol_rel=0.03):
    v0 = body.volume
    inp = ctx.extrudes.createInput(ctx.all_profiles(sk), ctx.ops.JoinFeatureOperation)
    inp.setSymmetricExtent(ctx.cbs(width_expr), True)
    inp.participantBodies = [body]
    f = ctx.extrudes.add(inp)
    f.name = label
    check_delta(label, v0, body.volume, want, tol_rel=tol_rel)
    return f


def combine_join(ctx, target, tools_list, label):
    tools = adsk.core.ObjectCollection.create()
    for t in tools_list:  # fusionhelper: allow R11 — collection add, not a document mutation
        tools.add(t)
    inp = ctx.root.features.combineFeatures.createInput(target, tools)
    inp.operation = ctx.ops.JoinFeatureOperation  # pyright: ignore[reportAttributeAccessIssue]
    inp.isKeepToolBodies = False
    f = ctx.root.features.combineFeatures.add(inp)
    f.name = label
    healthy_or_raise(ctx, label)
    return f


# ---------------------------------------------------------------- oracles

def web_column_delta(ctx, dz):
    """Volume four webs plus columns gain when web_z1 rises by dz (cm): the
    web footprint less its wall overlap, plus the column disc less the half
    inside the web."""
    v = ctx.val
    col_r, cav, half_w, r_col = v("col_r"), v("cavity_r"), v("web_w") / 2, v("col_d") / 2
    r_hi = cav + 0.1
    n = 200
    overlap = 0.0
    for i in range(n):
        u = -half_w + (i + 0.5) * (2 * half_w / n)
        overlap += max(0.0, r_hi - math.sqrt(cav * cav - u * u)) * (2 * half_w / n)
    web_area = 2 * half_w * (r_hi - col_r) - overlap
    col_area = PI * r_col ** 2 - PI * r_col ** 2 / 2       # the half beyond col_r lies in the web
    return 4 * (web_area + col_area) * dz


def roof_volume(ctx):
    """Volume above the plane z = roof_z + (r - col_r) within the column disc
    and the web rectangle, below web_z1, for r <= cavity_r. cm3, one column."""
    v = ctx.val
    col_r, cav, half_w, r_col = v("col_r"), v("cavity_r"), v("web_w") / 2, v("col_d") / 2
    top, roof_z = v("web_z1"), v("roof_z")
    n = 400
    r0, r1 = col_r - r_col, cav
    du = 2 * r_col / n
    dr = (r1 - r0) / n
    vol = 0.0
    for i in range(n):
        r = r0 + (i + 0.5) * dr
        for j in range(n):
            u = -r_col + (j + 0.5) * du
            in_col = (r - col_r) ** 2 + u * u <= r_col * r_col
            in_web = col_r <= r <= cav and abs(u) <= half_w
            if in_col or in_web:
                vol += max(0.0, top - (roof_z + (r - col_r))) * du * dr
    return vol


def block_added(ctx, half_u, h):
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

def raise_webs(ctx):
    cup = body_named(ctx, "cup")
    v0 = cup.volume
    p = ctx.up.itemByName("web_z1")
    if p.expression.replace(" ", "") != WEB_Z1_OLD.replace(" ", ""):
        raise RuntimeError("web_z1 is %r, expected %r before stage E" % (p.expression, WEB_Z1_OLD))
    p.expression = WEB_Z1_NEW  # fusionhelper: allow R5 — bodies re-resolved by name after the write
    adsk.doEvents()
    healthy_or_raise(ctx, "web_z1 -> 46")
    cup = body_named(ctx, "cup")
    want = web_column_delta(ctx, (ctx.val("web_z1") - 4.0))
    check_delta("web_z1 40 -> 46", v0, cup.volume, want, tol_rel=0.02)


def cut_roofs(ctx):
    v = ctx.val
    col_r, cav, r0 = v("col_r"), v("cavity_r"), v("roof_r0")
    roof_z, top = v("roof_z"), v("web_z1") + 0.1
    za, zb = roof_z - (col_r - r0), roof_z + (cav - col_r)
    want = roof_volume(ctx)
    for n, theta_deg in COL_ANGLES:
        th = math.radians(theta_deg)
        plane = plane_named(ctx, "web_%s_plane" % n)
        sk = ctx.root.sketches.add(plane)
        sk.name = "col_roof_%s_sk" % n
        # corners in model space, drawn then pinned by H/V dimensions from the origin
        pts = [(r0, za), (cav, zb), (cav, top), (r0, top)]
        sp = [sk.modelToSketchSpace(ctx.pt(r * math.cos(th), r * math.sin(th), z)) for r, z in pts]
        lines = sk.sketchCurves.sketchLines
        segs = []
        for i in range(4):
            a = segs[-1].endSketchPoint if segs else sp[0]
            b = sp[(i + 1) % 4] if i < 3 else segs[0].startSketchPoint
            segs.append(lines.addByTwoPoints(a, b))
        o = sk.sketchToModelSpace(ctx.pt(0, 0, 0))
        ex = sk.sketchToModelSpace(ctx.pt(1, 0, 0))
        radial_is_x = abs((ex.x - o.x) * math.cos(th) + (ex.y - o.y) * math.sin(th)) > abs(ex.z - o.z)
        gc = sk.geometricConstraints
        # Axis-aligned lines drawn through the API arrive with inferred H/V
        # constraints (eight corner dimensions over-constrained, measured
        # 2026-10-22), so: pin the slope line's two ends (4 dims), one dim
        # for the top edge, and the three H/V constraints stated explicitly.
        h_or_v = (gc.addVertical, gc.addHorizontal) if radial_is_x else (gc.addHorizontal, gc.addVertical)
        h_or_v[0](segs[1])      # B-C runs along z
        h_or_v[1](segs[2])      # C-D runs along r
        h_or_v[0](segs[3])      # D-A runs along z
        corners = [segs[0].startSketchPoint, segs[1].startSketchPoint]
        exprs = [("roof_r0", "roof_z - ( col_r - roof_r0 )"), ("cavity_r", "roof_z + ( cavity_r - col_r )")]
        for pt_, (r_expr, z_expr) in zip(corners, exprs):
            g = pt_.geometry
            anchor = ctx.pt(g.x + 0.3, g.y + 0.3, 0)
            d = sk.sketchDimensions.addDistanceDimension(sk.originPoint, pt_, ctx.dims_or.HorizontalDimensionOrientation, anchor)
            d.parameter.expression = r_expr if radial_is_x else z_expr
            d = sk.sketchDimensions.addDistanceDimension(sk.originPoint, pt_, ctx.dims_or.VerticalDimensionOrientation, anchor)
            d.parameter.expression = z_expr if radial_is_x else r_expr
            adsk.doEvents()
        c_pt = segs[2].startSketchPoint
        g = c_pt.geometry
        d = sk.sketchDimensions.addDistanceDimension(
            sk.originPoint, c_pt,
            ctx.dims_or.VerticalDimensionOrientation if radial_is_x else ctx.dims_or.HorizontalDimensionOrientation,
            ctx.pt(g.x + 0.3, g.y + 0.3, 0))
        d.parameter.expression = "web_z1 + 1 mm"
        adsk.doEvents()
        assert_landed(sk, th, (r0 * 10, cav * 10, za * 10, top * 10), "col_roof_%s" % n)
        cup = body_named(ctx, "cup")
        sym_cut_checked(ctx, sk, "web_w + 2 mm", cup, want, "col_roof_%s" % n, tol_rel=0.02)
        adsk.doEvents()


def add_pad_feet(ctx):
    v = ctx.val
    pad_r, t = v("pad_r"), v("pad_back_t")
    z0, z1 = v("floor_t"), v("pad_z0") - 0.1
    want = block_added(ctx, v("pad_w") / 2 + 0.2, z1 - z0)
    for name, theta_deg in PADS:
        th = math.radians(theta_deg)
        plane = plane_named(ctx, "pad_%s_radial" % name)
        sk = ctx.root.sketches.add(plane)
        sk.name = "pad_%s_foot_sk" % name
        radial_rect(ctx, sk, th, pad_r - t / 2, (z0 + z1) / 2, t / 2, (z1 - z0) / 2,
                    "pad_back_t", "pad_r - pad_back_t / 2", "pad_z0 - 1 mm - floor_t", "( floor_t + pad_z0 - 1 mm ) / 2")
        assert_landed(sk, th, ((pad_r - t) * 10, pad_r * 10, z0 * 10, z1 * 10), "pad_%s_foot" % name)
        base = body_named(ctx, "base")
        sym_join_checked(ctx, sk, "pad_w + 4 mm", base, want, "pad_%s_foot" % name)
        adsk.doEvents()


def merge_specks(ctx):
    cup = body_named(ctx, "cup")
    specks = [b for n in ("inlay_logo", "inlay_left", "inlay_right") for b in group(ctx, n) if b.volume < SPECK_CM3]
    if not specks:
        print("specks: none")
        return
    v_specks = sum(b.volume for b in specks)
    v0 = cup.volume
    print("specks: %d pieces, %.6f cm3: %s" % (len(specks), v_specks, [b.name for b in specks]))
    combine_join(ctx, cup, specks, "specks_join")
    cup = body_named(ctx, "cup")
    if abs(cup.volume - v0 - v_specks) > VOL_TOL:
        raise RuntimeError("specks: cup gained %.6f, wanted %.6f" % (cup.volume - v0, v_specks))
    print("specks joined into the cup; +%.6f cm3" % v_specks)


# ---------------------------------------------------------------- audit

def face_normal(face):
    ev = face.evaluator
    rng = ev.parametricRange()     # a BoundingBox2D in this API build (measured), not a tuple
    if rng is None:
        return None
    pmin, pmax = rng.minPoint, rng.maxPoint
    mid = adsk.core.Point2D.create((pmin.x + pmax.x) / 2, (pmin.y + pmax.y) / 2)
    ok, normals = ev.getNormalsAtParameters([mid])
    if not ok or not normals:
        return None
    # The evaluator already returns the face's OUTWARD normal: flipping on
    # isParamReversed made the base's underside read as up and the pad flats'
    # floors read as down (measured 2026-10-22).
    return normals[0]


def classify(ctx, body, face, inverted):
    """Return (flagged, class) for one face in print orientation."""
    v = ctx.val
    n = face_normal(face)
    if n is None:
        return False, "no-normal"
    nz = -n.z if inverted else n.z
    if nz >= OVERHANG_NZ:
        return False, "ok"
    bb = face.boundingBox
    z0, z1 = bb.minPoint.z * 10, bb.maxPoint.z * 10
    dx, dy = (bb.maxPoint.x - bb.minPoint.x) * 10, (bb.maxPoint.y - bb.minPoint.y) * 10
    cx, cy = (bb.minPoint.x + bb.maxPoint.x) * 5, (bb.minPoint.y + bb.maxPoint.y) * 5
    bed = v("drum_h") * 10 if inverted else 0.0
    if abs(z0 - bed) < 0.01 and abs(z1 - bed) < 0.01:
        return True, "bed"
    g = face.geometry
    if g.surfaceType == adsk.core.SurfaceTypes.CylinderSurfaceType and adsk.core.Cylinder.cast(g).radius * 10 <= 2.0:
        return True, "small hole"
    if g.surfaceType == adsk.core.SurfaceTypes.CylinderSurfaceType or g.surfaceType == adsk.core.SurfaceTypes.ConeSurfaceType:
        return True, "curved, sampled normal only"
    if inverted and abs(z0 - (v("drum_h") - v("art_pocket_d")) * 10) < 0.01:
        return True, "pocket floor (art fill rule)"
    # thinness = area / longest extent: rotation-invariant (a bounding-box
    # width test failed the 45 deg pads' segment faces, measured)
    longest = max(dx, dy, 1e-6)
    thin = face.area * 100 / longest
    if abs(cx) < 1.0 and abs(cy) < 1.0 and dx > 150 and dy > 150:
        thin = face.area * 100 / (PI * (dx + dy) / 2)     # an annulus: area over its mean circumference
    if thin <= LEDGE_MM:
        return True, "ledge <= 1.5 mm"
    if thin <= BRIDGE_MM:
        return True, "bridge <= 20 mm"
    return True, "UNCLASSIFIED"


def audit(ctx):
    bad = []
    for b in ctx.root.bRepBodies:
        inverted = b.name != "base"
        counts = {}
        for f in b.faces:
            flagged, cls = classify(ctx, b, f, inverted)
            if not flagged:
                continue
            counts[cls] = counts.get(cls, 0) + 1
            if cls == "UNCLASSIFIED":
                bb = f.boundingBox
                bad.append("%s: face area %.2f mm2, x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f" % (
                    b.name, f.area * 100, bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10,
                    bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10))
        print("audit %s (%s): %s" % (b.name, "inverted" if inverted else "as modelled",
                                     ", ".join("%s x%d" % kv for kv in sorted(counts.items())) or "no down-facing faces"))
    for line in bad:
        print("UNCLASSIFIED " + line)
    if bad:
        raise RuntimeError("overhang audit: %d unclassified down-facing faces" % len(bad))


# ---------------------------------------------------------------- exports and renders

def export(ctx):
    os.makedirs(EXPORT_DIR, exist_ok=True)
    em = ctx.des.exportManager
    step = em.createSTEPExportOptions(EXPORT_DIR + "/pi_drum.step")
    if not em.execute(step):
        raise RuntimeError("STEP export returned False")
    mf = em.createC3MFExportOptions(ctx.root, EXPORT_DIR + "/pi_drum.3mf")
    if not em.execute(mf):
        raise RuntimeError("3MF export returned False")
    for name in ("pi_drum.step", "pi_drum.3mf"):
        p = os.path.join(EXPORT_DIR, name)
        if not os.path.exists(p) or os.path.getsize(p) < 10000:
            raise RuntimeError("export %s missing or tiny" % name)
        print("export %s: %d bytes" % (name, os.path.getsize(p)))


def render(ctx):
    os.makedirs(RENDER_DIR, exist_ok=True)
    vp = ctx.app.activeViewport
    base, cup = body_named(ctx, "base"), body_named(ctx, "cup")
    inlays = [b for n in ("inlay_logo", "inlay_left", "inlay_right") for b in group(ctx, n)]
    views = (("iso", (30, -30, 25), True, True), ("front", (0, -40, 6), True, True), ("left", (-40, 0, 6), True, True),
             ("right", (40, 0, 6), True, True), ("top", (0, 0, 40), True, True),
             ("base_above", (0.01, 0, 40), False, True), ("cup_below", (0.01, 0, -40), True, False))
    for name, eye, show_cup, show_base in views:
        cup.isVisible, base.isVisible = show_cup, show_base
        for b in inlays:
            b.isVisible = show_cup
        cam = vp.camera
        cam.eye = ctx.pt(*eye)
        cam.target = ctx.pt(0, 0, 6 if abs(eye[2]) < 30 else 0)
        cam.upVector = adsk.core.Vector3D.create(0, 0, 1)  # fusionhelper: allow R6 — camera up vector for a render, not geometry
        cam.isFitView = True
        vp.camera = cam
        adsk.doEvents()
        vp.saveAsImageFile(os.path.join(RENDER_DIR, "pi_drum_stageE_%s.png" % name), 1600, 1200)
    cup.isVisible, base.isVisible = True, True
    for b in inlays:
        b.isVisible = True


def run(_context: str):
    app = adsk.core.Application.get()
    if not app.activeDocument.name.startswith(DOC_PREFIX):
        raise RuntimeError("wrong document %r" % app.activeDocument.name)
    ctx = BuildCtx(app)
    ensure_params(ctx)

    raise_webs(ctx)
    cut_roofs(ctx)
    add_pad_feet(ctx)
    merge_specks(ctx)
    adsk.doEvents()
    healthy_or_raise(ctx, "stage E")

    names = sorted(b.name for b in ctx.root.bRepBodies)
    print("bodies (%d): %s" % (len(names), names))
    audit(ctx)
    for b in ctx.root.bRepBodies:
        print("%s: %.4f cm3, %d faces" % (b.name, b.volume, b.faces.count))
    export(ctx)
    render(ctx)
    print("done")
