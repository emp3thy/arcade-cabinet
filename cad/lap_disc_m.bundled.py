"""Lap pad, D-014: the nested disc. Stage M -- the Street Fighter II logo
debossed into the plate's top face (2026-09-13), in the document that holds
stages A to L.

The logo was a Fusion decal (cad/lap_disc_logo.py, appearance only). It is now
geometry, so the print carries it whether or not the slicer paints it:

  sf2_solid     the letterforms, imported 1:1 from
                cad/art/logo/sf2_deboss_solid.dxf (7 closed polylines, 8
                profiles once Fusion regions them)
  sf2_deboss    a cut of logo_deboss down from the plate's top face through
                every profile of sf2_solid -- the whole logo footprint,
                counters included
  sf2_holes     the counters -- the enclosed eyes of the letterforms -- from
                cad/art/logo/sf2_deboss_holes.dxf (6 polylines, 6 profiles)
  sf2_counters  a join of logo_deboss back up under those six, returning them
                to flush so they read as islands standing in the recess

Placement is baked into the DXF. Both files are written in millimetres in
model coordinates -- solid x -58.500..58.479, y 43.000..102.777, so 116.98 x
59.78 mm with its bottom edge at y 43 -- and the import needs no move and no
scale. The script asserts that box, and asserts the sketch plane maps 1:1 and
unrotated into model space, so a units or scale mismatch fails on import
rather than landing a wrong-sized logo that Fusion is perfectly happy with.

Why that size: the band above the buttons is bounded below by the top button's
raised disc at y 41 and above by the plate rim at r 124.65. This leaves 2 mm to
the disc and 6.4 mm from the top corners to the rim, and is the practical
ceiling -- the round plate cuts the corners away faster than extra width buys,
so even at a 4 mm rim margin the logo only reaches about 120 mm.

Nothing prints unsupported: the recess floor is flat and faces up, and the
counters stand on that floor.

Known exception, measured 2026-09-13: the two imported sketches carry no
constraints and no dimensions -- the DXF is the placement, asserted on import
by check_placement -- so the verification block reports sketch.unconstrained
against both. That finding is correct and expected for imported art. Fixing
the geometry does not clear it: sweeping isFixed over all 2402 curves and
points takes about four minutes, leaves sketch.isFullyConstrained False
anyway (geometricConstraints stays 0, which is what the check reads), and is
reverted wholesale if the run is later rolled back. The sweep was removed.

Oracles: profile area times depth for the cut and again for the join, then the
recess floor read back as planar faces at plate_top_z - logo_deboss inside the
logo's box, whose area must be the solid area less the counters, and the
counter tops read back as separate planar faces at plate_top_z. The art pocket
(stage G) has a floor at the same depth elsewhere on the plate, so every face
sweep is filtered to the logo's own box.
"""
FH_ATTEMPT = 1
FH_OPTS = {
    "only_params": ["logo_deboss"],
    "liveness_budget_s": 240,
    "max_bodies": 6,
}
INTERFERENCE_ALLOWED = []
CLEARANCES = []
EXPECT_DEAD = []  # namespace is reused across executes
# fh-bundle: kit begin v2 00ca86d51507
"""The build kit: one canonical copy of the helpers every Fusion build
script used to copy-paste (measured drift: back_splices.py carried a
stale face-count blind_cut while the volume fixes lived only in
build16.py).

Author scripts do `from fusionhelper.buildkit import *`; the bundler
(fusionhelper.bundle) replaces that line with this file's source so a
single self-contained artifact reaches Fusion. Offline (tests, pyright)
this module imports like any other; inside Fusion the same text runs
inlined.

Validation policy (api-notes S14/S15): volume-threshold is the DEFAULT
for cuts and cut patterns; face-count is opt-in for small isolated holes
only. Pattern seed cuts must cut exactly ONE body (multi-body seeds fail
replication with R-Pattern85/PATTERN_FEATURES_NO_PASTE and no causal
error text).
"""
import adsk.core
import adsk.fusion

KIT_VERSION = "2"

__all__ = ["KIT_VERSION", "BuildCtx"]


class BuildCtx:
    """Per-run Fusion handles + helper methods. Create once at the top
    of run(): ctx = BuildCtx(adsk.core.Application.get())"""

    def __init__(self, app):
        self.app = app
        self.des = adsk.fusion.Design.cast(app.activeProduct)
        self.root = self.des.rootComponent
        self.up = self.des.userParameters
        self.extrudes = self.root.features.extrudeFeatures
        self.patterns = self.root.features.rectangularPatternFeatures
        self.planes = self.root.constructionPlanes
        self.ops = adsk.fusion.FeatureOperations
        self.dims_or = adsk.fusion.DimensionOrientations
        self.dirs = adsk.fusion.ExtentDirections
        self.pt = adsk.core.Point3D.create
        self.cbs = adsk.core.ValueInput.createByString
        self.x_axis = self.root.xConstructionAxis
        self.y_axis = self.root.yConstructionAxis
        self.U = (1.0, 0.0, 0.0)
        self.V = (0.0, 1.0, 0.0)
        self._resolved = {}
        self._circle_jitter = 0

    def val(self, name):
        return self.up.itemByName(name).value  # cm

    def plane_at_z(self, off_expr, name):
        pin = self.planes.createInput()
        pin.setByOffset(self.root.xYConstructionPlane, self.cbs(off_expr))
        pl = self.planes.add(pin)
        pl.name = name
        return pl

    def all_profiles(self, sk):
        coll = adsk.core.ObjectCollection.create()
        for pr in sk.profiles:  # fusionhelper: allow R11 — collection add, not a document mutation
            coll.add(pr)
        return coll

    def bound_rect2(self, sk, w, hu, hv, u_size=None, v_size=None,
                    u_pos=None, v_pos=None):
        """Constrained rectangle. w = world centre; position expressions
        are (centre_expr, half_size_expr) pairs — base is the CENTRE
        coordinate expression (measured: corner-based baselines snapped
        the board to the wrong quadrant)."""
        pt, U, V = self.pt, self.U, self.V
        dims_or = self.dims_or
        c = sk.modelToSketchSpace(pt(w[0], w[1], w[2]))
        pu = sk.modelToSketchSpace(pt(w[0] + U[0], w[1] + U[1], w[2] + U[2]))
        pv = sk.modelToSketchSpace(pt(w[0] + V[0], w[1] + V[1], w[2] + V[2]))
        if abs(pu.x - c.x) >= abs(pu.y - c.y):
            shx, shy = hu, hv
            ax = (u_size, u_pos, 1 if pu.x > c.x else -1)
            ay = (v_size, v_pos, 1 if pv.y > c.y else -1)
        else:
            shx, shy = hv, hu
            ax = (v_size, v_pos, 1 if pv.x > c.x else -1)
            ay = (u_size, u_pos, 1 if pu.y > c.y else -1)
        lines = sk.sketchCurves.sketchLines.addTwoPointRectangle(
            pt(c.x - shx, c.y - shy, 0), pt(c.x + shx, c.y + shy, 0))
        gc = sk.geometricConstraints
        h_line = None
        v_line = None
        for k in range(lines.count):
            ln = lines.item(k)
            s, e = ln.startSketchPoint.geometry, ln.endSketchPoint.geometry
            if abs(e.x - s.x) >= abs(e.y - s.y):
                gc.addHorizontal(ln)
                if h_line is None:
                    h_line = ln
            else:
                gc.addVertical(ln)
                if v_line is None:
                    v_line = ln
        if h_line is None or v_line is None:
            raise RuntimeError("rect missing axis-aligned line")
        corner = lines.item(0).startSketchPoint
        anchor = pt(c.x + shx + 0.5, c.y - shy - 0.5, 0)
        d = sk.sketchDimensions.addDistanceDimension(
            h_line.startSketchPoint, h_line.endSketchPoint,
            dims_or.HorizontalDimensionOrientation, anchor)
        d.parameter.expression = ax[0] if ax[0] else "%.4f mm" % (shx * 20)
        d = sk.sketchDimensions.addDistanceDimension(
            v_line.startSketchPoint, v_line.endSketchPoint,
            dims_or.VerticalDimensionOrientation, anchor)
        d.parameter.expression = ay[0] if ay[0] else "%.4f mm" % (shy * 20)
        for orient, half_sz, (_, pos, sign), cval in (
                (dims_or.HorizontalDimensionOrientation, shx, ax, c.x),
                (dims_or.VerticalDimensionOrientation, shy, ay, c.y)):
            d = sk.sketchDimensions.addDistanceDimension(
                sk.originPoint, corner, orient, anchor)
            if pos is None:
                d.parameter.expression = "%.4f mm" % (abs(cval - half_sz) * 10)
            else:
                # abs() is load-bearing: a distance dimension is unsigned,
                # so a corner expression that evaluates NEGATIVE (any rect
                # centred on the sketch origin, e.g. '0 mm - (9.65 mm)')
                # is stored negative but SNAPPED POSITIVE by the solver,
                # sliding the whole rectangle sideways by its full width.
                # Measured 2026-08-02; abs() confirmed valid in a Fusion
                # expression and keeps the dimension parametric.
                d.parameter.expression = "abs( %s %s (%s) )" % (
                    pos[0], "-" if sign > 0 else "+", pos[1])

    def bound_circle(self, sk, w, r_cm, dia_expr, x_pos=None, v_pos=None):
        """Jittered creation: coincident-coordinate circles trigger silent
        alignment inference then over-constrain (measured). Dims snap it."""
        pt, U = self.pt, self.U
        dims_or = self.dims_or
        c = sk.modelToSketchSpace(pt(w[0], w[1], w[2]))
        pu = sk.modelToSketchSpace(pt(w[0] + U[0], w[1] + U[1], w[2] + U[2]))
        self._circle_jitter += 1
        j = self._circle_jitter
        circle = sk.sketchCurves.sketchCircles.addByCenterRadius(
            pt(c.x + 0.011 + 0.003 * j, c.y + 0.017 + 0.005 * j, 0), r_cm)
        anchor = pt(c.x + r_cm + 0.4, c.y - 0.4, 0)
        if abs(pu.x - c.x) >= abs(pu.y - c.y):
            h_pos, v_pos_ = x_pos, v_pos
        else:
            h_pos, v_pos_ = v_pos, x_pos
        d = sk.sketchDimensions.addDistanceDimension(
            sk.originPoint, circle.centerSketchPoint,
            dims_or.HorizontalDimensionOrientation, anchor)
        d.parameter.expression = (h_pos if h_pos
                                  else "%.4f mm" % (abs(c.x) * 10))
        d = sk.sketchDimensions.addDistanceDimension(
            sk.originPoint, circle.centerSketchPoint,
            dims_or.VerticalDimensionOrientation, anchor)
        d.parameter.expression = (v_pos_ if v_pos_
                                  else "%.4f mm" % (abs(c.y) * 10))
        d = sk.sketchDimensions.addDiameterDimension(circle, anchor)
        d.parameter.expression = dia_expr
        return circle

    # ---- cuts and joins (volume-threshold validation by default) --------

    def _one_side(self, inp, dist_expr, direction):
        ext = adsk.fusion.DistanceExtentDefinition.create(self.cbs(dist_expr))
        inp.setOneSideExtent(ext, direction)

    def _try_dirs(self, kind):
        if kind in self._resolved:
            return (self._resolved[kind], None)
        return (self.dirs.PositiveExtentDirection,
                self.dirs.NegativeExtentDirection)

    def faces_of(self, bodies):
        return sum(b.faces.count for b in bodies)

    def through_cut(self, profs, depth_expr, participants, *,
                    min_vol_cm3=0.02):
        """Symmetric through-cut. Volume-validated (S14/S15: face counts
        can stay flat or DROP on seam-spanning cuts)."""
        return self.sym_cut(profs, depth_expr, participants,
                            min_vol_cm3=min_vol_cm3)

    def sym_cut(self, profs, depth_expr, participants, *, min_vol_cm3=0.02):
        v0 = sum(b.volume for b in participants)
        inp = self.extrudes.createInput(profs, self.ops.CutFeatureOperation)
        inp.setSymmetricExtent(self.cbs(depth_expr), True)
        inp.participantBodies = participants
        f = self.extrudes.add(inp)
        if v0 - sum(b.volume for b in participants) <= min_vol_cm3:
            f.deleteMe()
            raise RuntimeError("symmetric cut removed no volume")
        return f

    def blind_cut(self, profs, dist_expr, participants, kind="cut", *,
                  min_vol_cm3=0.02):
        v0 = sum(b.volume for b in participants)
        for d in self._try_dirs(kind):
            adsk.doEvents()
            if d is None:
                break
            inp = self.extrudes.createInput(
                profs, self.ops.CutFeatureOperation)
            self._one_side(inp, dist_expr, d)
            inp.participantBodies = participants
            f = self.extrudes.add(inp)
            if v0 - sum(b.volume for b in participants) > min_vol_cm3:
                self._resolved[kind] = d
                return f
            f.deleteMe()
        raise RuntimeError("blind cut cut nothing (%s)" % kind)

    def checked_join(self, profs, dist_expr, target, predicate, kind):
        for d in self._try_dirs(kind):
            adsk.doEvents()
            if d is None:
                break
            inp = self.extrudes.createInput(
                profs, self.ops.JoinFeatureOperation)
            self._one_side(inp, dist_expr, d)
            inp.participantBodies = [target]
            f = self.extrudes.add(inp)
            if predicate(target):
                self._resolved[kind] = d
                return f
            f.deleteMe()
        raise RuntimeError("join never satisfied predicate (%s)" % kind)

    def checked_newbody(self, profs, dist_expr, predicate, kind):
        for d in self._try_dirs(kind):
            adsk.doEvents()
            if d is None:
                break
            inp = self.extrudes.createInput(
                profs, self.ops.NewBodyFeatureOperation)
            self._one_side(inp, dist_expr, d)
            f = self.extrudes.add(inp)
            body = f.bodies.item(0)
            if predicate(body):
                self._resolved[kind] = d
                return f, body
            f.deleteMe()
        raise RuntimeError("new body never satisfied predicate (%s)" % kind)

    # ---- patterns -------------------------------------------------------

    def _pattern(self, coll, ax, n, d, validate, adjust):
        """Direction/compute retry ladder. NOTE (S15, measured): a seed
        CUT that removes material from more than one body never
        replicates (R-Pattern85 / PATTERN_FEATURES_NO_PASTE, no causal
        error text) — reshape the seed to cut exactly one body."""
        healthy = (
            adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState,
            adsk.fusion.FeatureHealthStates.WarningFeatureHealthState)
        reasons = []
        perp = self.y_axis if ax == self.x_axis else self.x_axis
        popts = adsk.fusion.PatternComputeOptions
        modes = ((popts.AdjustPatternCompute, popts.IdenticalPatternCompute)
                 if adjust else (None,))
        for dd in (d, "-(%s)" % d):
            adsk.doEvents()
            for mode in modes:
                adsk.doEvents()
                inp = self.patterns.createInput(
                    coll, ax, self.cbs(n), self.cbs(dd),
                    adsk.fusion.PatternDistanceType
                    .SpacingPatternDistanceType)
                inp.setDirectionTwo(perp, self.cbs("1"), self.cbs("0 mm"))
                if mode is not None:
                    inp.patternComputeOption = mode  # pyright: ignore[reportAttributeAccessIssue]
                try:
                    f = self.patterns.add(inp)
                except Exception as e:
                    reasons.append("%s/%s add-raise %s"
                                   % (dd, mode, str(e)[:50]))
                    continue
                if f.healthState in healthy and validate(f):
                    return f
                reasons.append("%s/%s hs=%s" % (dd, mode, f.healthState))
                f.deleteMe()
        raise RuntimeError("pattern never validated: " + " | ".join(reasons))

    def pattern_bodies(self, bodies, ax, n, d, predicate):
        """Body pattern (no compute-option: body patterns reject it).
        predicate(feature) -> bool accepts/rejects the whole pattern —
        e.g. a bounds check that every new body landed inside the part."""
        coll = adsk.core.ObjectCollection.create()
        for b in bodies:  # fusionhelper: allow R11 — collection add, not a document mutation
            coll.add(b)
        f = self._pattern(coll, ax, n, d, predicate, adjust=False)
        out = []
        for i in range(f.bodies.count):
            out.append(f.bodies.item(i))
        return out

    def pattern_cut(self, feats, ax, n, d, watch, *,
                    min_vol_cm3=None, min_new_faces=None):
        """Pattern of cut features. Volume threshold is the default
        choice (S14/S15); face-count is opt-in for small isolated holes.
        Exactly one of min_vol_cm3 / min_new_faces must be given."""
        if (min_vol_cm3 is None) == (min_new_faces is None):
            raise ValueError(
                "pass exactly one of min_vol_cm3 / min_new_faces")
        coll = adsk.core.ObjectCollection.create()
        for f in feats:  # fusionhelper: allow R11 — collection add, not a document mutation
            coll.add(f)
        if min_vol_cm3 is not None:
            v0 = sum(b.volume for b in watch)

            def validate(_f):
                return v0 - sum(b.volume for b in watch) >= min_vol_cm3
        else:
            before = self.faces_of(watch)

            def validate(_f):
                return self.faces_of(watch) - before >= min_new_faces  # pyright: ignore[reportOperatorIssue]
        return self._pattern(coll, ax, n, d, validate, adjust=True)
# fh-bundle: kit end

import adsk.core
import adsk.fusion

ART = r"C:\Users\gethi\source\arcade-cabinet\cad\art\logo"
DXF = {
    "sf2_solid": ART + "\\sf2_deboss_solid.dxf",
    "sf2_holes": ART + "\\sf2_deboss_holes.dxf",
}

PARAMS_M = (
    ("logo_deboss", "0.6 mm", "mm",
     "Street Fighter II logo recess depth in the plate top"),
)
NEEDED = ("plate_top_z", "plate_t")

# What each DXF must land on, in mm, in model coordinates: x0, x1, y0, y1.
# Measured from the files' own vertices, so this is the import's oracle.
BOX = {
    "sf2_solid": (-58.500, 58.479, 43.000, 102.777),
    "sf2_holes": (-28.717, 30.219, 56.232, 94.030),
}
BOX_TOL = 0.05     # mm, on every edge of the imported box
AREA_TOL = 0.02    # fraction, on volumes derived from profile area
EPS = 0.002        # cm, face and plane coincidence


def ensure_params(ctx):
    for name in NEEDED:
        if ctx.up.itemByName(name) is None:
            raise RuntimeError("parameter %s missing: run stages A to L first" % name)
    for name, expr, unit, comment in PARAMS_M:
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


def plane_named(ctx, name):
    pl = ctx.root.constructionPlanes.itemByName(name)
    if pl is None:
        raise RuntimeError("no construction plane named %s: run stages A to L first" % name)
    return pl


def feature_exists(ctx, name):
    for n in (name, name + " (1)"):
        if ctx.extrudes.itemByName(n) is not None:
            return True
    return False


def check_placement(ctx, sk, name):
    """The sketch plane must map 1:1 and unrotated onto the plate's top face,
    and the imported box must be the DXF's own box. Derived at runtime rather
    than assumed (R6)."""
    o = sk.sketchToModelSpace(ctx.pt(0.0, 0.0, 0.0))
    ux = sk.sketchToModelSpace(ctx.pt(1.0, 0.0, 0.0))
    uy = sk.sketchToModelSpace(ctx.pt(0.0, 1.0, 0.0))
    ztop = ctx.val("plate_top_z")
    if abs(o.z - ztop) > EPS:
        raise RuntimeError("%s sits at z %.3f mm, wanted the plate top %.3f"
                           % (name, o.z * 10, ztop * 10))
    for got, want, lbl in (((ux.x - o.x, ux.y - o.y, ux.z - o.z), (1.0, 0.0, 0.0), "u"),
                           ((uy.x - o.x, uy.y - o.y, uy.z - o.z), (0.0, 1.0, 0.0), "v")):
        if max(abs(g - w) for g, w in zip(got, want)) > 1.0e-6:
            raise RuntimeError("%s %s axis maps to %s, wanted %s -- the plane is "
                               "rotated or mirrored" % (name, lbl, got, want))
    bb = sk.boundingBox
    got = (bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10, bb.maxPoint.y * 10)
    for g, w, lbl in zip(got, BOX[name], ("x0", "x1", "y0", "y1")):
        if abs(g - w) > BOX_TOL:
            raise RuntimeError("%s %s landed at %.3f mm, wanted %.3f -- DXF units "
                               "or scale wrong" % (name, lbl, g, w))
    print("%s: %d curves, %d profiles, x %.2f..%.2f y %.2f..%.2f mm on the plate top"
          % (name, sk.sketchCurves.count, sk.profiles.count, got[0], got[1], got[2], got[3]))


def import_dxf(ctx, name, plane):
    """Import one DXF onto plane as a single sketch, named name."""
    before = set(s.name for s in ctx.root.sketches)
    opts = ctx.app.importManager.createDXF2DImportOptions(DXF[name], plane)
    opts.isSingleSketchResult = True
    ctx.app.importManager.importToTarget2(opts, ctx.root)
    adsk.doEvents()
    fresh = [s for s in ctx.root.sketches if s.name not in before]
    if len(fresh) != 1:
        raise RuntimeError("%s: the import made %d sketches, wanted 1"
                           % (name, len(fresh)))
    sk = fresh[0]
    sk.name = name
    adsk.doEvents()
    check_placement(ctx, sk, name)
    return sk


def sketch_area(sk):
    return sum(pr.areaProperties().area for pr in sk.profiles)


def cut_named(ctx, profs, dist_expr, body_name, want_cm3, tol, kind):
    """Blind cut whose direction is resolved by what it removes, not assumed."""
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


def join_named(ctx, profs, dist_expr, body_name, want_cm3, tol, kind):
    """Join on an already-resolved direction. Volume alone cannot tell a join
    that fills the recess from one that stands proud of the top face -- both
    add the same -- so kind is shared with the cut and the direction comes from
    it. The body is re-resolved by name after every mutation (R5)."""
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
        added = body_named(ctx, body_name).volume - v0
        if abs(added - want_cm3) < tol * want_cm3:
            ctx._resolved[kind] = d
            return f, added
        f.deleteMe()
        adsk.doEvents()
    raise RuntimeError("%s: no direction added %.4f cm3" % (kind, want_cm3))


def flat_faces_at(body, z_cm, box_mm, pad_mm=1.0):
    """Up-facing planar faces lying at z_cm, whose whole extent is inside
    box_mm. The box filter keeps the stage G art pocket -- same 0.6 mm depth,
    other side of the plate -- out of the sweep."""
    x0, x1, y0, y1 = (v / 10.0 for v in box_mm)
    pad = pad_mm / 10.0
    out = []
    for f in body.faces:
        pl = adsk.core.Plane.cast(f.geometry)
        if pl is None or pl.normal.z < 0.999:
            continue
        bb = f.boundingBox
        if abs(bb.maxPoint.z - z_cm) > EPS or abs(bb.minPoint.z - z_cm) > EPS:
            continue
        if (bb.minPoint.x < x0 - pad or bb.maxPoint.x > x1 + pad
                or bb.minPoint.y < y0 - pad or bb.maxPoint.y > y1 + pad):
            continue
        out.append(f)
    return out


def read_back(ctx, area_solid, area_holes):
    plate = body_named(ctx, "plate")
    ztop = ctx.val("plate_top_z")
    depth = ctx.val("logo_deboss")
    box = BOX["sf2_solid"]

    floor = flat_faces_at(plate, ztop - depth, box)
    got = sum(f.area for f in floor)
    want = area_solid - area_holes
    if abs(got - want) > AREA_TOL * want:
        raise RuntimeError("recess floor is %.4f cm2 over %d faces, wanted %.4f"
                           % (got, len(floor), want))
    print("recess floor %.4f cm2 at z %.2f mm (%d faces), wanted %.4f"
          % (got, (ztop - depth) * 10, len(floor), want))

    tops = flat_faces_at(plate, ztop, box)
    got = sum(f.area for f in tops)
    if len(tops) != ctx.root.sketches.itemByName("sf2_holes").profiles.count:
        raise RuntimeError("%d counter tops at the plate top, wanted %d"
                           % (len(tops), ctx.root.sketches.itemByName("sf2_holes").profiles.count))
    if abs(got - area_holes) > AREA_TOL * area_holes:
        raise RuntimeError("counter tops are %.4f cm2, wanted %.4f" % (got, area_holes))
    print("%d counters flush at z %.2f mm, %.4f cm2, wanted %.4f"
          % (len(tops), ztop * 10, got, area_holes))

    if plate.boundingBox.maxPoint.z - ztop < 0.0:
        raise RuntimeError("the plate no longer reaches its top face")


def run(_context: str):
    app = adsk.core.Application.get()
    if not app.activeDocument.name.startswith("Arcade Controller"):
        raise RuntimeError("wrong document " + app.activeDocument.name)
    ctx = BuildCtx(app)
    ensure_params(ctx)
    healthy = adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState
    plane = plane_named(ctx, "plate_top_plane")

    built = feature_exists(ctx, "sf2_deboss")
    if built:
        # A 1000-curve sketch takes tens of minutes to delete, so an existing
        # stage M is re-verified in place, never torn down and redrawn.
        solid = ctx.root.sketches.itemByName("sf2_solid")
        holes = ctx.root.sketches.itemByName("sf2_holes")
        if solid is None or holes is None:
            raise RuntimeError("sf2_deboss exists without its sketches")
        for sk, name in ((solid, "sf2_solid"), (holes, "sf2_holes")):
            check_placement(ctx, sk, name)
        print("stage M already built; verifying in place")
    else:
        solid = import_dxf(ctx, "sf2_solid", plane)
        area = sketch_area(solid)
        want = area * ctx.val("logo_deboss")
        f, removed = cut_named(ctx, ctx.all_profiles(solid), "logo_deboss",
                               "plate", want, AREA_TOL, "sf2_depth")
        f.name = "sf2_deboss"
        print("sf2_deboss: -%.4f cm3 over %.4f cm2 (want %.4f)" % (removed, area, want))

        holes = import_dxf(ctx, "sf2_holes", plane)
        area_h = sketch_area(holes)
        want_h = area_h * ctx.val("logo_deboss")
        f, added = join_named(ctx, ctx.all_profiles(holes), "logo_deboss",
                              "plate", want_h, AREA_TOL, "sf2_depth")
        f.name = "sf2_counters"
        print("sf2_counters: +%.4f cm3 over %.4f cm2 (want %.4f)" % (added, area_h, want_h))
    adsk.doEvents()

    read_back(ctx, sketch_area(solid), sketch_area(holes))

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


# fusionhelper: verification stub v1
def _fh_verify_entry():
    import os, json, traceback
    home = os.environ.get('FUSIONHELPER_HOME') or os.path.join(
        os.environ.get('LOCALAPPDATA', ''), 'FusionHelper')

    def _bail(code, msg):
        return 'FH_VERDICT1 ' + json.dumps(
            {'v': 1, 'status': 'error', 'code': code, 'msg': msg, 'home': home},
            separators=(',', ':'))

    try:
        with open(os.path.join(home, 'fh_verify.py'), encoding='utf-8') as f:
            src = f.read()
    except Exception as e:
        return _bail('verify.block_missing', str(e))
    ns: dict = {'__name__': 'fh_verify'}   # annotated: else pyright infers dict[str, str]
    try:
        exec(compile(src, 'fh_verify.py', 'exec'), ns)
        g = globals()
        return ns['fh_verify'](
            clearances=g.get('CLEARANCES'),
            face_specs=g.get('FACE_SPECS'),
            datum_heights_cm=g.get('DATUM_HEIGHTS_CM'),
            digest=g.get('DIGEST'),
            interference_allowed=g.get('INTERFERENCE_ALLOWED'),
            expect_dead=g.get('EXPECT_DEAD'),
            refs=g.get('FH_REFS', {}),
            attempt=g.get('FH_ATTEMPT', 1),
            **g.get('FH_OPTS', {}))
    except Exception:
        return _bail('verify.internal', traceback.format_exc()[-600:])


def _fh_wrap(inner):
    def _wrapped(_context: str):
        inner(_context)                 # NOT wrapped: build exceptions must escape
        print(_fh_verify_entry())
    return _wrapped


run = _fh_wrap(run)
