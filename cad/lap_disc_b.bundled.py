"""Lap pad, D-014: the nested disc. Stage B -- runs in the document that holds
stage A (cad/lap_disc.py) and adds, in order:

  rim slope    a distance-and-angle chamfer on the shell's outer top edge:
               rim_slope_w across the top, rim_slope_h down the wall, so the
               rim band falls from shell_h at the lip to shell_h - rim_slope_h
               at the outside. A flat lip rim_lip_w wide survives at the
               rebate. Both flips are tried; the one that leaves the outer
               wall's top at shell_h - rim_slope_h is kept (predicate, R4).
  raised discs disc_h proud on the plate: stick_disc_d round the stick (the
               shaft hole and the four M3 holes stay open), btn_disc_d round
               each button. Annular profiles only, selected by loop count so
               no hole is filled.
  tyre ridges  two rings ridge_t proud and ridge_h tall on the outer wall at
               ridge_lo_z and ridge_hi_z: they locate the TPU tyre.
  port boss    a block joined inside the rear wall, then a flat facet_w wide
               cut across the outside at facet_y, leaving a flat wall
               boss_in thick for the port board (window is stage C).

Every feature is guarded by name so the script is idempotent in the document.
Stage A parameters must already exist with their stage A expressions.
"""
FH_ATTEMPT = 1
FH_OPTS = {
    "only_params": [
        "rim_slope_h", "rim_lip_w", "disc_h", "stick_disc_d", "btn_disc_d",
        "ridge_t", "ridge_h", "ridge_lo_z", "ridge_hi_z", "facet_w", "boss_in",
    ],
    "liveness_budget_s": 120,
}
INTERFERENCE_ALLOWED = []
CLEARANCES = []
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

PARAMS_B = (
    ("rim_slope_h",   "7 mm",  "mm",  "rim band drop from the lip to the outer wall"),
    ("rim_lip_w",     "2 mm",  "mm",  "flat lip left beside the plate rebate"),
    ("rim_slope_w",   "(shell_dia - rebate_dia) / 2 - rim_lip_w", "mm", "derived: slope run"),
    ("rim_slope_ang", "atan(rim_slope_h / rim_slope_w)", "deg", "derived"),
    ("disc_h",        "2 mm",  "mm",  "raised discs on the plate"),
    ("stick_disc_d",  "90 mm", "mm",  "raised disc round the stick"),
    ("btn_disc_d",    "36 mm", "mm",  "raised disc round each button; 4 mm short of the 40 pitch"),
    ("ridge_t",       "0.8 mm", "mm", "tyre ridge proud of the wall"),
    ("ridge_h",       "2 mm",  "mm",  "tyre ridge height"),
    ("ridge_lo_z",    "5 mm",  "mm",  "lower tyre ridge, bottom face"),
    ("ridge_hi_z",    "41 mm", "mm",  "upper tyre ridge, bottom face"),
    ("ridge_od",      "shell_dia + 2 * ridge_t", "mm", "derived"),
    ("facet_w",       "64 mm", "mm",  "port facet chord width on the rear wall"),
    ("facet_y",       "sqrt((shell_dia / 2) ^ 2 - (facet_w / 2) ^ 2)", "mm", "derived: facet plane from the centre"),
    ("boss_in",       "8 mm",  "mm",  "flat wall thickness behind the facet"),
    # boss_w == facet_w and boss_y1 == facet_y: a wider or deeper boss pokes its
    # corners through the round wall into the tyre (measured 2026-09-12: 70 x
    # 0.75 x 34 mm clash with boss_w = facet_w + 6, boss_y1 = r - 1).
    ("boss_w",        "facet_w", "mm", "derived: boss exactly the facet chord"),
    ("boss_y0",       "facet_y - boss_in", "mm", "derived: boss inner face"),
    ("boss_y1",       "facet_y", "mm", "derived: boss outer face is the facet plane"),
)

BUTTONS = ("lp", "mp", "hp", "lk", "mk", "hk")
STAGE_A_ROOTS = ("shell_dia", "shell_h", "rebate_dia", "plate_t", "stick_x",
                 "stick_y", "stick_hole", "stick_bolt_r", "bolt_hole", "btn_hole",
                 "plate_top_z", "under_h", "floor_t")


def ensure_params(ctx):
    for name in STAGE_A_ROOTS:
        if ctx.up.itemByName(name) is None:
            raise RuntimeError("stage A parameter %s missing: run lap_disc.py first" % name)
    for name, expr, unit, comment in PARAMS_B:
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
    """Sketches and features share one name namespace: a feature named like
    its sketch is auto-suffixed " (1)" (measured 2026-09-12), so both
    spellings are checked."""
    for coll in (ctx.extrudes, ctx.root.features.chamferFeatures):
        for n in (name, name + " (1)"):
            if coll.itemByName(n) is not None:
                return True
    return False


def centred_circle(ctx, sk, r_seed_cm, dia_expr, jitter):
    c = sk.sketchCurves.sketchCircles.addByCenterRadius(
        ctx.pt(0.011 + 0.003 * jitter, 0.017 + 0.005 * jitter, 0), r_seed_cm)
    sk.geometricConstraints.addCoincident(c.centerSketchPoint, sk.originPoint)
    d = sk.sketchDimensions.addDiameterDimension(c, ctx.pt(r_seed_cm + 0.4, -0.4, 0))
    d.parameter.expression = dia_expr
    return c


def concentric_circle(ctx, sk, ref_circle, r_seed_cm, dia_expr, jitter):
    """Second circle on an already-dimensioned centre: concentric + diameter."""
    rc = ref_circle.centerSketchPoint.geometry
    c = sk.sketchCurves.sketchCircles.addByCenterRadius(
        ctx.pt(rc.x + 0.004 * jitter, rc.y + 0.006 * jitter, 0), r_seed_cm)
    sk.geometricConstraints.addConcentric(ref_circle, c)
    d = sk.sketchDimensions.addDiameterDimension(
        c, ctx.pt(rc.x + r_seed_cm + 0.3, rc.y - 0.3, 0))
    d.parameter.expression = dia_expr
    return c


def axis_circle(ctx, sk, ref_circle, dx_cm, dy_cm, r_seed_cm, dia_expr,
                dist_expr, jitter):
    gc = sk.geometricConstraints
    rc = ref_circle.centerSketchPoint.geometry
    c = sk.sketchCurves.sketchCircles.addByCenterRadius(
        ctx.pt(rc.x + dx_cm + 0.002 * jitter, rc.y + dy_cm + 0.003 * jitter, 0),
        r_seed_cm)
    anchor = ctx.pt(rc.x + dx_cm + r_seed_cm + 0.3, rc.y + dy_cm - 0.3, 0)
    if abs(dx_cm) >= abs(dy_cm):
        gc.addHorizontalPoints(ref_circle.centerSketchPoint, c.centerSketchPoint)
        orient = ctx.dims_or.HorizontalDimensionOrientation
    else:
        gc.addVerticalPoints(ref_circle.centerSketchPoint, c.centerSketchPoint)
        orient = ctx.dims_or.VerticalDimensionOrientation
    d = sk.sketchDimensions.addDistanceDimension(
        ref_circle.centerSketchPoint, c.centerSketchPoint, orient, anchor)
    d.parameter.expression = dist_expr
    d = sk.sketchDimensions.addDiameterDimension(c, anchor)
    d.parameter.expression = dia_expr
    return c


def annular_profiles(sk):
    coll = adsk.core.ObjectCollection.create()
    n = 0
    for pr in sk.profiles:  # fusionhelper: allow R11 — collection add, not a document mutation
        if pr.profileLoops.count >= 2:
            coll.add(pr)
            n += 1
    if n == 0:
        raise RuntimeError("%s: no annular profile" % sk.name)
    return coll, n


def outer_wall_top_z(ctx, shell, r_cm):
    best = None
    for face in shell.faces:
        cyl = adsk.core.Cylinder.cast(face.geometry)
        if cyl is None or abs(cyl.radius - r_cm) > 0.005:
            continue
        z = face.boundingBox.maxPoint.z
        if best is None or z > best:
            best = z
    if best is None:
        raise RuntimeError("no cylindrical face of radius %.3f cm on the shell" % r_cm)
    return best


def run(_context: str):
    ctx = BuildCtx(adsk.core.Application.get())
    ensure_params(ctx)
    v = ctx.val
    shell = body_named(ctx, "shell")
    plate = body_named(ctx, "plate")
    r_out = v("shell_dia") / 2

    # ---- rim slope: chamfer on the outer top edge ------------------------
    if not feature_exists(ctx, "rim_slope"):
        edges = adsk.core.ObjectCollection.create()
        for e in shell.edges:
            circ = adsk.core.Circle3D.cast(e.geometry)
            if circ is None:
                continue
            if abs(circ.radius - r_out) < 0.005 and abs(circ.center.z - v("shell_h")) < 0.005:
                edges.add(e)
        if edges.count != 1:
            raise RuntimeError("expected one outer top edge, found %d" % edges.count)
        want_z = v("shell_h") - v("rim_slope_h")
        chamfers = ctx.root.features.chamferFeatures
        healthy = adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState
        done = False
        for flipped in (False, True):
            adsk.doEvents()
            ci = chamfers.createInput2()
            ci.chamferEdgeSets.addDistanceAndAngleChamferEdgeSet(
                edges, ctx.cbs("rim_slope_w"), ctx.cbs("rim_slope_ang"), flipped, False)
            f = chamfers.add(ci)
            shell = body_named(ctx, "shell")
            if f.healthState == healthy and abs(outer_wall_top_z(ctx, shell, r_out) - want_z) < 0.01:
                f.name = "rim_slope"
                done = True
                break
            f.deleteMe()
        if not done:
            raise RuntimeError("rim slope chamfer never left the outer wall top at %.2f cm" % want_z)
        shell = body_named(ctx, "shell")
        print("rim slope: outer wall top at %.2f mm, flipped=%s" % (outer_wall_top_z(ctx, shell, r_out) * 10, flipped))
    adsk.doEvents()

    # ---- raised discs on the plate ----------------------------------------
    if not feature_exists(ctx, "raised_discs"):
        plate_top = ctx.planes.itemByName("plate_top_plane")
        if plate_top is None:
            raise RuntimeError("plate_top_plane missing")
        sk = ctx.root.sketches.add(plate_top)
        sk.name = "raised_discs"
        z = v("plate_top_z")
        stick_in = ctx.bound_circle(
            sk, (v("stick_x"), v("stick_y"), z), v("stick_hole") / 2, "stick_hole",
            x_pos="abs(stick_x)", v_pos="abs(stick_y)")
        concentric_circle(ctx, sk, stick_in, v("stick_disc_d") / 2, "stick_disc_d", 1)
        br = v("stick_bolt_r")
        for k, (dx, dy) in enumerate(((br, 0), (-br, 0), (0, br), (0, -br))):
            axis_circle(ctx, sk, stick_in, dx, dy, v("bolt_hole") / 2, "bolt_hole",
                        "stick_bolt_r", k + 1)
        for i, name in enumerate(BUTTONS):
            inner = ctx.bound_circle(
                sk, (v(name + "_x"), v(name + "_y"), z), v("btn_hole") / 2, "btn_hole",
                x_pos="abs(%s_x)" % name, v_pos="abs(%s_y)" % name)
            concentric_circle(ctx, sk, inner, v("btn_disc_d") / 2, "btn_disc_d", i + 2)
            adsk.doEvents()
        if not sk.isFullyConstrained:
            loose = [i for i, c in enumerate(sk.sketchCurves.sketchCircles)
                     if not c.isFullyConstrained]
            raise RuntimeError("raised_discs loose circles: %s" % loose)
        profs, n = annular_profiles(sk)
        if n != 7:
            raise RuntimeError("raised_discs expected 7 annular profiles, got %d" % n)
        v0 = plate.volume
        f = ctx.checked_join(
            profs, "disc_h", plate,
            lambda b: b.volume - v0 > 1.4, "discs")
        f.name = "raised_discs"
        plate = body_named(ctx, "plate")
        print("raised discs: plate +%.2f cm3" % (plate.volume - v0))
    adsk.doEvents()

    # ---- tyre ridges on the outer wall -----------------------------------
    for tag, zp in (("lo", "ridge_lo_z"), ("hi", "ridge_hi_z")):
        name = "tyre_ridge_" + tag
        if feature_exists(ctx, name):
            continue
        pl = ctx.planes.itemByName(name + "_plane")
        if pl is None:
            pl = ctx.plane_at_z(zp, name + "_plane")
        sk = ctx.root.sketches.add(pl)
        sk.name = name
        inner = centred_circle(ctx, sk, r_out, "shell_dia", 1)
        concentric_circle(ctx, sk, inner, v("ridge_od") / 2, "ridge_od", 2)
        if not sk.isFullyConstrained:
            raise RuntimeError("%s sketch not fully constrained" % name)
        profs, n = annular_profiles(sk)
        if n != 1:
            raise RuntimeError("%s expected 1 annular profile, got %d" % (name, n))
        v0 = shell.volume
        f = ctx.checked_join(
            profs, "ridge_h", shell,
            lambda b: b.volume - v0 > 1.0, name)
        f.name = name
        shell = body_named(ctx, "shell")
        print("%s: shell +%.2f cm3" % (name, shell.volume - v0))
        adsk.doEvents()

    # ---- port boss inside the rear wall, then the flat facet --------------
    if not feature_exists(ctx, "port_boss"):
        fl = ctx.planes.itemByName("floor_plane")
        if fl is None:
            raise RuntimeError("floor_plane missing")
        sk = ctx.root.sketches.add(fl)
        sk.name = "port_boss"
        yc = (v("boss_y0") + v("boss_y1")) / 2
        ctx.bound_rect2(
            sk, (0, yc, v("floor_t")),
            v("boss_w") / 2, (v("boss_y1") - v("boss_y0")) / 2,
            u_size="boss_w", v_size="boss_y1 - boss_y0",
            u_pos=("0 mm", "boss_w / 2"), v_pos=("(boss_y0 + boss_y1) / 2", "(boss_y1 - boss_y0) / 2"))
        if not sk.isFullyConstrained:
            raise RuntimeError("port_boss sketch not fully constrained")
        v0 = shell.volume
        f = ctx.checked_join(
            ctx.all_profiles(sk), "under_h - floor_t", shell,
            lambda b: b.volume - v0 > 5.0, "boss")
        f.name = "port_boss"
        shell = body_named(ctx, "shell")
        print("port boss: shell +%.2f cm3" % (shell.volume - v0))
    adsk.doEvents()

    if not feature_exists(ctx, "port_facet"):
        sk = ctx.root.sketches.add(ctx.root.xYConstructionPlane)
        sk.name = "port_facet"
        y0 = v("facet_y")
        y1 = r_out + 1.0
        ctx.bound_rect2(
            sk, (0, (y0 + y1) / 2, 0),
            v("facet_w") / 2 + 1.0, (y1 - y0) / 2,
            u_size="facet_w + 20 mm", v_size="shell_dia / 2 + 10 mm - facet_y",
            u_pos=("0 mm", "(facet_w + 20 mm) / 2"),
            v_pos=("(facet_y + shell_dia / 2 + 10 mm) / 2", "(shell_dia / 2 + 10 mm - facet_y) / 2"))
        if not sk.isFullyConstrained:
            raise RuntimeError("port_facet sketch not fully constrained")
        f = ctx.blind_cut(ctx.all_profiles(sk), "shell_h + 1 mm", [shell], "facet",
                          min_vol_cm3=0.5)
        f.name = "port_facet"
        shell = body_named(ctx, "shell")
        flat = None
        for face in shell.faces:
            pln = adsk.core.Plane.cast(face.geometry)
            if pln is None:
                continue
            n = pln.normal
            if abs(n.y) > 0.999 and abs(face.boundingBox.maxPoint.y - y0) < 0.01:
                flat = face
        if flat is None:
            raise RuntimeError("no flat facet face at y = %.2f cm" % y0)
        bb = flat.boundingBox
        print("port facet: flat %.1f wide x %.1f tall at y %.2f mm" % (
            (bb.maxPoint.x - bb.minPoint.x) * 10, (bb.maxPoint.z - bb.minPoint.z) * 10, y0 * 10))
    adsk.doEvents()

    for b in (body_named(ctx, "shell"), body_named(ctx, "plate")):
        bb = b.boundingBox
        print("%s: %.3f x %.3f x %.3f mm, z %.3f..%.3f, %.2f cm3, %d faces" % (
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
