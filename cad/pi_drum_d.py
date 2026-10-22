"""Pi console drum, D-021. Stage D -- the livery (plan task 6), in the
document that holds stages A to C.

Three wrapped debosses inlay_d deep into the cup's outer wall, each with a
separate red body for the H2D's second nozzle:

  logo    cad/art/drum/sf2_front.dxf (letterforms) and sf2_front_holes.dxf
          (counters) on art_front, the XZ plane offset -drum_r; centred at
          z 67 on the front (-y)
  left    cad/art/drum/chunli_side.dxf on art_left, the YZ plane offset
          -drum_r; centred at z 67, facing the front
  right   the same DXF on art_right, YZ offset +drum_r (mirror image of the
          left, so she faces the front there too; Ryu replaces it when
          OI-012 supplies art)

The DXF is the placement (stage M's rule): each import is mapped into
model space and asserted against the box the art script printed, so a
units, scale or plane-mapping slip raises before anything is cut. The
plane mappings were measured by cad/pi_drum_d_probe.py.

How an inlay is made (both mechanisms proven in scratch-document spikes
on 2026-10-22): copy the cup, deboss the cup, inlay = copy minus cup.
The logo's counters (the enclosed eyes of the letters) are done with whole
bodies rather than by picking recess-floor faces letter by letter: a
second and third pristine copy give counters = copyC minus (copyB with the
holes debossed); then the counters are cut out of the inlay and joined
back into the cup, so the eyes read as drum-coloured islands in the red
letters. Every step asserts its volume: deboss = sum(profile areas) x
inlay_d x ((drum_r - inlay_d/2) / drum_r); copies are exact; booleans to
1e-6 cm3.

Known exception, as stage M: the imported sketches carry no constraints or
dimensions, so the verification block reports sketch.unconstrained
against them; force_liveness keeps the liveness pass running.
"""
FH_ATTEMPT = 7
FH_OPTS = {
    "only_params": ["inlay_d"],
    "liveness_budget_s": 600,
    # 5 if every inlay merges into one body; up to 2 + 7 + 5 + 5 if Fusion
    # keeps the disconnected pieces separate (read_back asserts the groups)
    "max_bodies": 20,
    # the imported art sketches fail the constraints check by design (stage M)
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
ART_DIR = r"C:/Users/gethi/sources/arcade-cabinet/.claude/worktrees/pi-drum/cad/art/drum"
RENDER_DIR = r"C:/Users/gethi/sources/arcade-cabinet/.claude/worktrees/pi-drum/cad/renders"
PI = math.pi
MM = 0.1
BOX_TOL = 0.05   # mm, placement assertions
VOL_TOL = 1e-6   # cm3, boolean identities
SLIVER_CM2 = 0.005   # profiles below this (0.5 mm2) are regioning slivers, not art

NEEDED = ("drum_r", "wall_t", "split_z", "drum_h")
PARAMS = (
    ("inlay_d", "1.2 mm", "mm", "deboss depth into the 3 mm wall; the red inlay's thickness"),
)
# (name, dxf, plane base, offset expr, model-space box: axis-a range, z range, fixed axis value)
# boxes are what drum_art.py printed, mapped through the measured plane mappings
ART = (
    ("sf2_front",       "sf2_front.dxf",       "xz", "-drum_r", "x", (-58.489, 58.489), (37.112, 96.888), ("y", -80.0)),
    ("sf2_front_holes", "sf2_front_holes.dxf", "xz", "-drum_r", "x", (-29.468, 29.468), (48.101, 85.899), ("y", -80.0)),
    ("sil_left",        "chunli_side.dxf",     "yz", "-drum_r", "y", (-22.410, 22.410), (37.501, 96.499), ("x", -80.0)),
    ("sil_right",       "chunli_side.dxf",     "yz", "drum_r",  "y", (-22.410, 22.410), (37.501, 96.499), ("x", 80.0)),
)
BAND_Z = (35.0, 99.0)   # the outer cylindrical face that carries the livery spans at least this, mm


# ---------------------------------------------------------------- helpers

def ensure_params(ctx):
    for name in NEEDED:
        if ctx.up.itemByName(name) is None:
            raise RuntimeError("parameter %s missing: run stages A to C first" % name)
    for name, expr, unit, comment in PARAMS:
        existing = ctx.up.itemByName(name)
        if existing is not None:
            if existing.expression.replace(" ", "") != expr.replace(" ", ""):
                raise RuntimeError("parameter %s already exists with expression %r, wanted %r"
                                   % (name, existing.expression, expr))
            continue
        ctx.up.add(name, ctx.cbs(expr), unit, comment)
        adsk.doEvents()


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


def check(label, got, want, tol):
    if abs(got - want) > tol:
        raise RuntimeError("%s: got %.6f, wanted %.6f" % (label, got, want))
    print("%s: %.6f (want %.6f)" % (label, got, want))


def offset_plane(ctx, base_name, off_expr, name):
    base = ctx.root.xZConstructionPlane if base_name == "xz" else ctx.root.yZConstructionPlane
    pin = ctx.planes.createInput()
    pin.setByOffset(base, ctx.cbs(off_expr))
    pl = ctx.planes.add(pin)
    pl.name = name
    return pl


def import_dxf(ctx, spec, plane):
    """Import one DXF onto plane as a single sketch, assert where it landed
    in model space (the DXF is the placement), return the sketch."""
    name, dxf, _, _, axis, a_range, z_range, (fixed_axis, fixed_val) = spec
    before = set(s.name for s in ctx.root.sketches)
    opts = ctx.app.importManager.createDXF2DImportOptions(os.path.join(ART_DIR, dxf), plane)
    opts.isSingleSketchResult = True
    ctx.app.importManager.importToTarget2(opts, ctx.root)
    adsk.doEvents()
    fresh = [s for s in ctx.root.sketches if s.name not in before]
    if len(fresh) != 1:
        raise RuntimeError("%s: the import made %d sketches, wanted 1" % (name, len(fresh)))
    sk = fresh[0]
    sk.name = name
    adsk.doEvents()
    bb = sk.boundingBox
    corners = [sk.sketchToModelSpace(ctx.pt(x, y, 0)) for x in (bb.minPoint.x, bb.maxPoint.x)
               for y in (bb.minPoint.y, bb.maxPoint.y)]
    pick = {"x": lambda p: p.x, "y": lambda p: p.y}
    a_vals = [pick[axis](p) * 10 for p in corners]
    z_vals = [p.z * 10 for p in corners]
    f_vals = [pick[fixed_axis](p) * 10 for p in corners]
    got = (min(a_vals), max(a_vals), min(z_vals), max(z_vals))
    want = a_range + z_range
    for g, w, lbl in zip(got, want, (axis + "0", axis + "1", "z0", "z1")):
        if abs(g - w) > BOX_TOL:
            raise RuntimeError("%s: %s landed at %.3f mm, wanted %.3f -- units, scale or plane mapping wrong"
                               % (name, lbl, g, w))
    if max(abs(f - fixed_val) for f in f_vals) > BOX_TOL:
        raise RuntimeError("%s: sketch plane at %s %.3f, wanted %.3f" % (name, fixed_axis, f_vals[0], fixed_val))
    print("%s: %d curves, %d profiles, %s %.2f..%.2f z %.2f..%.2f at %s %.1f"
          % (name, sk.sketchCurves.count, sk.profiles.count, axis, got[0], got[1], got[2], got[3], fixed_axis, fixed_val))
    return sk


def profiles_of(sk):
    return [sk.profiles.item(i) for i in range(sk.profiles.count)]


def sketch_area(sk):
    return sum(p.areaProperties().area for p in profiles_of(sk))


def outer_band_face(ctx, body, label):
    """The one cylindrical face of radius drum_r on body whose z range covers BAND_Z."""
    r = ctx.val("drum_r")
    hits = []
    for f in body.faces:
        g = f.geometry
        if g.surfaceType == adsk.core.SurfaceTypes.CylinderSurfaceType:
            if abs(adsk.core.Cylinder.cast(g).radius - r) < 1e-4:
                bb = f.boundingBox
                if bb.minPoint.z * 10 <= BAND_Z[0] and bb.maxPoint.z * 10 >= BAND_Z[1]:
                    hits.append(f)
    if len(hits) != 1:
        raise RuntimeError("%s: %d outer band faces of r %.1f spanning z %s, wanted 1" % (label, len(hits), r * 10, BAND_Z))
    return hits[0]


def copy_body(ctx, body, name):
    coll = adsk.core.ObjectCollection.create()
    coll.add(body)
    f = ctx.root.features.copyPasteBodies.add(coll)
    c = f.bodies.item(0)
    c.name = name
    check("copy %s volume" % name, c.volume, body.volume, VOL_TOL)
    return c


def deboss(ctx, body, sk, depth_expr, label):
    """Wrapped emboss of every profile of sk into body's outer band, depth
    depth_expr (negative = deboss), ONE FEATURE PER PROFILE: handed the
    eight logo profiles together, createInput raised "Input profiles are
    not coplanar" (measured 2026-10-22) although they share a sketch. The
    regions never overlap, so the summed removal is the union's. Returns
    the removed volume."""
    v0 = body.volume
    emb = ctx.root.features.embossFeatures
    profs = profiles_of(sk)
    # Order: a profile whose box lies inside another profile's box is an
    # island (Fusion regions a keyhole loop into a ring and its island) and
    # must be embossed BEFORE its ring, or it no longer lies on the band face
    # (measured 2026-10-22: logo_deboss_4 "cannot create emboss at specified
    # depth" when embossed fourth).
    boxes = []
    for p in profs:
        bb = p.boundingBox
        boxes.append((bb.minPoint.x, bb.minPoint.y, bb.maxPoint.x, bb.maxPoint.y))
    def inside_another(i):
        x0, y0, x1, y1 = boxes[i]
        return any(j != i and boxes[j][0] <= x0 and boxes[j][1] <= y0 and boxes[j][2] >= x1 and boxes[j][3] >= y1
                   for j in range(len(boxes)))
    order = sorted(range(len(profs)), key=lambda i: (0 if inside_another(i) else 1, i))
    for i in order:
        x0, y0, x1, y1 = boxes[i]
        print("%s profile %d: area %.4f cm2, box %.2f..%.2f x %.2f..%.2f mm%s" % (
            label, i + 1, profs[i].areaProperties().area, x0 * 10, x1 * 10, y0 * 10, y1 * 10,
            ", island" if inside_another(i) else ""))
    # Fusion's regioning of the logo loops also yields a sliver (profile 4,
    # area 0.0000 cm2 in a 0.05 x 0.02 mm box, measured 2026-10-22) that no
    # emboss can be created from; skip anything under SLIVER_CM2 and build
    # the oracle from the areas actually embossed.
    area = 0.0
    n = 0
    for i in order:
        a = profs[i].areaProperties().area
        if a < SLIVER_CM2:
            print("%s profile %d skipped: sliver, %.6f cm2" % (label, i + 1, a))
            continue
        face = outer_band_face(ctx, body, label)
        f = emb.add(emb.createInput([profs[i]], [face], ctx.cbs(depth_expr)))
        n += 1
        f.name = "%s_%d" % (label, n)
        area += a
        adsk.doEvents()
    healthy_or_raise(ctx, label)
    print("%s: %d of %d profiles embossed, %.4f cm2" % (label, n, len(profs), area))
    return v0 - body.volume, area


def combine(ctx, target, tool, operation, keep_tool, label):
    tools = adsk.core.ObjectCollection.create()
    tools.add(tool)
    inp = ctx.root.features.combineFeatures.createInput(target, tools)
    inp.operation = operation  # pyright: ignore[reportAttributeAccessIssue]
    inp.isKeepToolBodies = keep_tool
    f = ctx.root.features.combineFeatures.add(inp)
    f.name = label
    healthy_or_raise(ctx, label)
    return f


def expected_deboss(ctx, area_cm2):
    r, d = ctx.val("drum_r"), ctx.val("inlay_d")
    return area_cm2 * d * ((r - d / 2) / r)


# A boolean whose result is disconnected comes back as several bodies named
# "<name>", "<name> (1)", ... (measured 2026-10-22: the logo inlay arrived as
# one body per letter and body_named saw only the eighth letter's 0.3457
# cm3). These helpers treat such a set as one group.

def group(ctx, name):
    return [b for b in ctx.root.bRepBodies if b.name == name or b.name.startswith(name + " (")]


def group_volume(bodies):
    return sum(b.volume for b in bodies)


def merge_group(ctx, name, label):
    """Try to join the group into one body (Fusion allows disjoint lumps in
    one body). If the join is unhealthy or the count does not drop, undo it
    and keep the pieces: the slicer takes either."""
    bodies = group(ctx, name)
    if len(bodies) <= 1:
        return bodies
    v = group_volume(bodies)
    tools = adsk.core.ObjectCollection.create()
    for b in bodies[1:]:  # fusionhelper: allow R11 — collection add, not a document mutation
        tools.add(b)
    inp = ctx.root.features.combineFeatures.createInput(bodies[0], tools)
    inp.operation = ctx.ops.JoinFeatureOperation  # pyright: ignore[reportAttributeAccessIssue]
    inp.isKeepToolBodies = False
    f = ctx.root.features.combineFeatures.add(inp)
    f.name = label
    after = group(ctx, name)
    ok = (f.healthState == adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState
          and len(after) == 1 and abs(group_volume(after) - v) < VOL_TOL)
    if not ok:
        print("%s: join of %d pieces not accepted (health %s, %d after); keeping the pieces" % (
            label, len(bodies), f.healthState, len(after)))
        f.deleteMe()
        return group(ctx, name)
    print("%s: %d pieces joined into one body, %.6f cm3" % (label, len(bodies), after[0].volume))
    return after


def bbox_centre_mm(b):
    bb = b.boundingBox
    return ((bb.minPoint.x + bb.maxPoint.x) * 5, (bb.minPoint.y + bb.maxPoint.y) * 5, (bb.minPoint.z + bb.maxPoint.z) * 5)


def containing_piece(pieces, point_mm):
    x, y, z = point_mm
    for p in pieces:
        bb = p.boundingBox
        if bb.minPoint.x * 10 <= x <= bb.maxPoint.x * 10 and bb.minPoint.y * 10 <= y <= bb.maxPoint.y * 10 \
                and bb.minPoint.z * 10 <= z <= bb.maxPoint.z * 10:
            return p
    raise RuntimeError("no piece's box contains (%.1f, %.1f, %.1f)" % point_mm)


# ---------------------------------------------------------------- build

def build_inlay(ctx, cup, sk, inlay_name, label):
    """copy, deboss, inlay = copy - cup (a group of pieces). Returns the
    removed volume; the pieces are found by group(ctx, inlay_name)."""
    copy_body(ctx, cup, inlay_name)
    removed, area = deboss(ctx, cup, sk, "-inlay_d", label + "_deboss")
    check(label + "_deboss volume", removed, expected_deboss(ctx, area), 0.005 * removed)
    combine(ctx, body_named(ctx, inlay_name), body_named(ctx, "cup"), ctx.ops.CutFeatureOperation, True, label + "_inlay")
    pieces = group(ctx, inlay_name)
    check(label + "_inlay volume (%d pieces)" % len(pieces), group_volume(pieces), removed, VOL_TOL)
    return removed


def build_logo2(ctx, cup, sk_solid, sk_holes):
    """Two pristine copies first (one to be debossed with the holes, one to
    become the counters), then the logo inlay, then the counters: counters =
    copy_d minus copy_c, each cut out of the one letter that contains it,
    then all joined back into the cup."""
    v_cup0 = cup.volume
    copy_body(ctx, cup, "logo_holes_tmp")      # will be debossed with the holes
    copy_body(ctx, cup, "logo_counters")       # becomes the counters
    removed = build_inlay(ctx, cup, sk_solid, "inlay_logo", "logo")
    copy_c = body_named(ctx, "logo_holes_tmp")
    removed_holes, holes_area = deboss(ctx, copy_c, sk_holes, "-inlay_d", "logo_holes_deboss")
    check("logo_holes_deboss volume", removed_holes, expected_deboss(ctx, holes_area), 0.005 * removed_holes)
    combine(ctx, body_named(ctx, "logo_counters"), body_named(ctx, "logo_holes_tmp"),
            ctx.ops.CutFeatureOperation, False, "logo_counters_body")
    counters = group(ctx, "logo_counters")
    check("logo_counters volume (%d pieces)" % len(counters), group_volume(counters), removed_holes, VOL_TOL)
    # each counter out of the letter that contains it. Letter boxes overlap,
    # so a box test picked the wrong letter twice (measured: 2 of 6 cuts
    # removed nothing); candidates are tried by point containment first and
    # every cut must remove the counter's volume or it is undone.
    for k, c in enumerate(list(counters)):
        c_vol = c.volume
        centre = bbox_centre_mm(c)
        pt = adsk.core.Point3D.create(centre[0] * MM, centre[1] * MM, centre[2] * MM)
        pieces = group(ctx, "inlay_logo")
        cands = [p for p in pieces if p.pointContainment(pt) == adsk.fusion.PointContainment.PointInsidePointContainment]
        cands += [p for p in pieces if p not in cands]
        done = False
        for letter in cands:
            v_letter = letter.volume
            f = combine(ctx, letter, c, ctx.ops.CutFeatureOperation, True, "logo_eye_%d" % (k + 1))
            adsk.doEvents()
            if abs((v_letter - letter.volume) - c_vol) < VOL_TOL:
                done = True
                break
            f.deleteMe()
            adsk.doEvents()
        if not done:
            raise RuntimeError("counter %d (%.6f cm3) cut no letter" % (k + 1, c_vol))
        print("logo_eye_%d: %.6f cm3 out of its letter" % (k + 1, c_vol))
    pieces = group(ctx, "inlay_logo")
    check("inlay_logo less counters (%d pieces)" % len(pieces), group_volume(pieces), removed - removed_holes, VOL_TOL)
    # all counters back into the cup
    cup = body_named(ctx, "cup")
    v_cup = cup.volume
    tools = adsk.core.ObjectCollection.create()
    for c in group(ctx, "logo_counters"):  # fusionhelper: allow R11 — collection add, not a document mutation
        tools.add(c)
    inp = ctx.root.features.combineFeatures.createInput(cup, tools)
    inp.operation = ctx.ops.JoinFeatureOperation  # pyright: ignore[reportAttributeAccessIssue]
    inp.isKeepToolBodies = False
    f = ctx.root.features.combineFeatures.add(inp)
    f.name = "logo_counters_join"
    healthy_or_raise(ctx, "logo_counters_join")
    cup = body_named(ctx, "cup")
    check("cup with counters back", cup.volume, v_cup + removed_holes, VOL_TOL)
    check("cup net logo removal", v_cup0 - cup.volume, removed - removed_holes, VOL_TOL)
    if group(ctx, "logo_counters") or group(ctx, "logo_holes_tmp"):
        raise RuntimeError("temporary logo bodies survived: %s" % [b.name for b in ctx.root.bRepBodies])
    merge_group(ctx, "inlay_logo", "logo_inlay_merge")


def group_bbox_mm(bodies):
    xs, ys, zs = [], [], []
    for b in bodies:
        bb = b.boundingBox
        xs += [bb.minPoint.x * 10, bb.maxPoint.x * 10]
        ys += [bb.minPoint.y * 10, bb.maxPoint.y * 10]
        zs += [bb.minPoint.z * 10, bb.maxPoint.z * 10]
    return min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)


def read_back(ctx):
    others = sorted(b.name for b in ctx.root.bRepBodies
                    if not any(b.name == n or b.name.startswith(n + " (") for n in ("inlay_logo", "inlay_left", "inlay_right")))
    if others != ["base", "cup"]:
        raise RuntimeError("unexpected bodies: %s" % others)
    r = ctx.val("drum_r") * 10
    d = ctx.val("inlay_d") * 10
    for name, zr, axis in (("inlay_logo", (37.112, 96.888), "y"), ("inlay_left", (37.501, 96.499), "x"), ("inlay_right", (37.501, 96.499), "x")):
        pieces = group(ctx, name)
        if not pieces:
            raise RuntimeError("no %s bodies" % name)
        x0, x1, y0, y1, z0, z1 = group_bbox_mm(pieces)
        if abs(z0 - zr[0]) > 0.1 or abs(z1 - zr[1]) > 0.1:
            raise RuntimeError("%s spans z %.2f..%.2f, wanted %.2f..%.2f" % (name, z0, z1, zr[0], zr[1]))
        # The outer skin of a wrapped inlay touches r = drum_r on its axis; its
        # bounding box says nothing radial beyond that (the logo wraps 84 deg,
        # so its box reaches in to 58.7 mm, measured). Depth is checked by the
        # containment scan below.
        hi = max(abs(x0), abs(x1)) if axis == "x" else max(abs(y0), abs(y1))
        if abs(hi - r) > 0.05:
            raise RuntimeError("%s outer extent %.2f, wanted %.2f" % (name, hi, r))
        print("%s: %d piece(s), z %.2f..%.2f, outer %s %.2f, %.4f cm3" % (name, len(pieces), z0, z1, axis, hi, group_volume(pieces)))
    # the inlay sits in the cup's recess: a point on the inlay's outer skin is
    # solid in the inlay and empty in the cup; d/2 deeper than the recess is cup
    cup = body_named(ctx, "cup")
    left = group(ctx, "inlay_left")
    _, _, _, _, z0, z1 = group_bbox_mm(left)
    zc = (z0 + z1) / 2 * MM
    inside_pc = adsk.fusion.PointContainment.PointInsidePointContainment
    found = False
    for i in range(-20, 21):
        y = i * 0.1   # cm
        p_in = adsk.core.Point3D.create(-(r - 0.3) * MM, y, zc)
        if any(p.pointContainment(p_in) == inside_pc for p in left):
            if cup.pointContainment(p_in) == inside_pc:
                raise RuntimeError("cup is solid inside the left inlay at y %.1f" % (y * 10))
            p_under = adsk.core.Point3D.create(-(r - d - 0.5) * MM, y, zc)
            if cup.pointContainment(p_under) != inside_pc:
                raise RuntimeError("cup is empty under the left inlay at y %.1f" % (y * 10))
            found = True
            print("left inlay: recess confirmed at y %.1f z %.1f" % (y * 10, zc * 10))
            break
    if not found:
        raise RuntimeError("no inlay material found on the left scan line")


def render(ctx, tag):
    os.makedirs(RENDER_DIR, exist_ok=True)
    vp = ctx.app.activeViewport
    for name, orient in (("front", adsk.core.ViewOrientations.FrontViewOrientation),
                         ("left", adsk.core.ViewOrientations.LeftViewOrientation),
                         ("right", adsk.core.ViewOrientations.RightViewOrientation),
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
    cup = body_named(ctx, "cup")

    planes = {}
    for spec in ART:
        key = (spec[2], spec[3])
        if key not in planes:
            planes[key] = offset_plane(ctx, spec[2], spec[3], "art_" + ("front" if spec[2] == "xz" else ("left" if spec[3].startswith("-") else "right")))
    sketches = {spec[0]: import_dxf(ctx, spec, planes[(spec[2], spec[3])]) for spec in ART}
    adsk.doEvents()

    build_logo2(ctx, cup, sketches["sf2_front"], sketches["sf2_front_holes"])
    cup = body_named(ctx, "cup")
    build_inlay(ctx, cup, sketches["sil_left"], "inlay_left", "left")
    merge_group(ctx, "inlay_left", "left_inlay_merge")
    cup = body_named(ctx, "cup")
    build_inlay(ctx, cup, sketches["sil_right"], "inlay_right", "right")
    merge_group(ctx, "inlay_right", "right_inlay_merge")
    adsk.doEvents()

    healthy_or_raise(ctx, "stage D")
    read_back(ctx)
    for b in ctx.root.bRepBodies:
        print("%s: %.4f cm3, %d faces" % (b.name, b.volume, b.faces.count))
    render(ctx, "D")
    print("done")
