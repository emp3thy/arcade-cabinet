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
