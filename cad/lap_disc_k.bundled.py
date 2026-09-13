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
