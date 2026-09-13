"""Lap pad, D-014: the nested disc. Stage C -- internals and soft parts, in the
document that holds stages A and B. Adds, in order:

  brook standoffs  four so_od posts so_h tall with a so_pilot hole, on the
                   ASSUMED 88 x 37 pitch (OI: measure), board centre at
                   (brook_cx, brook_cy).
  lipo tray        a wall tray_wall thick, tray_h tall, round a lipo_w x
                   lipo_d pocket with tray_clear a side, centred at
                   (lipo_cx, lipo_cy). Sits behind the stick body.
  coil boss        coil_boss_d disc coil_boss_h proud of the underside at
                   (coil_x, coil_y): the Qi receiver's outside face.
  antenna bracket  an ant_t plate, ant_len deep, ant_h tall, standing on the
                   floor inside the front wall at x = ant_x, with an ant_hole
                   clearance hole along x at ant_hole_z for the bulkhead.
  port window      port_w x port_h through the flat facet wall from stage B,
                   centred on x = 0, z = port_cz. The board's two M3 holes
                   (ASSUMED 24 x 20 diagonal) land inside the window and are
                   not cut; stage D once the board is measured.
  tpu ring         separate body: ring_id to ring_od, ring_t thick below the
                   floor, with a ring_coil_hole over the coil boss.
  tpu tyre         separate body: shell_dia to tyre_od between the two ridges.

Sketches on XZ- and YZ-offset planes probe their own mapping (R6): the plane
is created, the sketch origin is read back in model space, and the plane is
rebuilt with a negated offset if it landed on the wrong side.
"""
FH_ATTEMPT = 2
FH_OPTS = {
    "only_params": [
        "brook_cx", "brook_cy", "brook_pitch_x", "brook_pitch_y", "so_od", "so_h", "so_pilot",
        "lipo_w", "lipo_d", "lipo_cx", "lipo_cy", "tray_clear", "tray_wall", "tray_h",
        "coil_x", "coil_y", "coil_boss_d", "coil_boss_h",
        "ant_x", "ant_t", "ant_len", "ant_h", "ant_hole", "ant_hole_z", "ant_gap",
        "port_w", "port_h", "port_cz",
        "ring_id", "ring_od", "ring_t", "ring_coil_hole", "tyre_od",
    ],
    "liveness_budget_s": 180,
}
INTERFERENCE_ALLOWED = []
CLEARANCES = []
# The four standoffs move symmetrically about the board centre when a pitch
# changes: volume, area, bbox and centroid stay identical, so the signature
# probe reads both pitches as dead (attempt 1, measured). They are live: the
# script steps brook_pitch_x and reads the standoff axes back.
EXPECT_DEAD = ["brook_pitch_x", "brook_pitch_y"]
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

PARAMS_C = (
    ("brook_cx",      "48 mm",   "mm", "Brook board centre x (board 96 x 45 at x 0..96, y 50..95)"),
    ("brook_cy",      "72.5 mm", "mm", "Brook board centre y"),
    ("brook_pitch_x", "88 mm",   "mm", "ASSUMED Brook hole pitch along x; measure"),
    ("brook_pitch_y", "37 mm",   "mm", "ASSUMED Brook hole pitch along y; measure"),
    ("so_od",         "7 mm",    "mm", "standoff outer diameter"),
    ("so_h",          "5 mm",    "mm", "standoff height above the floor"),
    ("so_pilot",      "2.5 mm",  "mm", "M3 thread-forming pilot"),
    ("lipo_w",        "95 mm",   "mm", "LiPo 103395 along x"),
    ("lipo_d",        "33 mm",   "mm", "LiPo 103395 along y"),
    ("lipo_cx",       "-67.5 mm", "mm", "LiPo centre x"),
    ("lipo_cy",       "42.5 mm", "mm", "LiPo centre y; 3 mm behind the stick body"),
    ("tray_clear",    "1 mm",    "mm", "tray clearance a side"),
    ("tray_wall",     "2 mm",    "mm", "tray wall"),
    ("tray_h",        "6 mm",    "mm", "tray wall height above the floor"),
    ("tray_in_w",     "lipo_w + 2 * tray_clear", "mm", "derived"),
    ("tray_in_d",     "lipo_d + 2 * tray_clear", "mm", "derived"),
    ("tray_out_w",    "tray_in_w + 2 * tray_wall", "mm", "derived"),
    ("tray_out_d",    "tray_in_d + 2 * tray_wall", "mm", "derived"),
    ("tray_top_z",    "floor_t + tray_h", "mm", "derived"),
    ("coil_x",        "35 mm",   "mm", "Qi coil centre x, under the right palm"),
    ("coil_y",        "-95 mm",  "mm", "Qi coil centre y"),
    ("coil_boss_d",   "62 mm",   "mm", "coil boss diameter"),
    ("coil_boss_h",   "3 mm",    "mm", "coil boss proud of the underside"),
    ("ant_x",         "-30 mm",  "mm", "antenna bracket plate, x of its mid-plane"),
    ("ant_t",         "2.5 mm",  "mm", "antenna bracket thickness"),
    ("ant_len",       "16 mm",   "mm", "antenna bracket depth from the wall"),
    ("ant_h",         "18 mm",   "mm", "antenna bracket height above the floor"),
    ("ant_hole",      "6.5 mm",  "mm", "bulkhead clearance hole"),
    ("ant_hole_z",    "14 mm",   "mm", "bulkhead axis height above the floor datum"),
    ("ant_gap",       "1 mm",    "mm", "antenna bracket gap to the inner wall"),
    # derived from the wall so a combined parameter step cannot push the bracket
    # through it (attempt 1: edit.introduces_clash with a literal -124 mm)
    ("ant_cy",        "-(sqrt((cavity_dia / 2) ^ 2 - ant_x ^ 2) - ant_gap - ant_len / 2)", "mm", "derived: bracket centre y, just inside the front wall"),
    ("ant_top_z",     "floor_t + ant_h", "mm", "derived"),
    ("port_w",        "30.4 mm", "mm", "port board window width"),
    ("port_h",        "26.4 mm", "mm", "port board window height"),
    ("port_cz",       "24.2 mm", "mm", "port window centre height"),
    ("ring_id",       "110 mm",  "mm", "TPU ring inner diameter"),
    ("ring_od",       "280 mm",  "mm", "TPU ring outer diameter"),
    ("ring_t",        "6 mm",    "mm", "TPU ring thickness below the floor"),
    ("ring_coil_hole", "66 mm",  "mm", "TPU ring hole over the coil boss"),
    ("tyre_od",       "300 mm",  "mm", "TPU tyre outer diameter"),
    ("tyre_z0",       "ridge_lo_z + ridge_h", "mm", "derived: tyre sits on the lower ridge"),
    ("tyre_h",        "ridge_hi_z - tyre_z0", "mm", "derived: up to the upper ridge"),
)

NEEDED = ("shell_dia", "shell_h", "floor_t", "under_h", "facet_y", "boss_in",
          "ridge_lo_z", "ridge_hi_z", "ridge_h", "cavity_dia")
# parameters whose expression may be rewritten in an existing document
UPDATABLE = ("ant_cy",)


def ensure_params(ctx):
    for name in NEEDED:
        if ctx.up.itemByName(name) is None:
            raise RuntimeError("parameter %s missing: run stages A and B first" % name)
    for name, expr, unit, comment in PARAMS_C:
        existing = ctx.up.itemByName(name)
        if existing is not None:
            if existing.expression.replace(" ", "") != expr.replace(" ", ""):
                if name in UPDATABLE:
                    existing.expression = expr
                    adsk.doEvents()
                    continue
                raise RuntimeError(
                    "parameter %s already exists with expression %r, wanted %r"
                    % (name, existing.expression, expr))
            continue
        # ant_gap must exist before ant_cy's expression references it: PARAMS_C
        # lists it first, so plain order suffices.
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
    """Sketches and features share one name namespace: a feature named like
    its sketch is auto-suffixed " (1)" (measured 2026-09-12), so both
    spellings are checked."""
    for n in (name, name + " (1)"):
        if ctx.extrudes.itemByName(n) is not None:
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
    rc = ref_circle.centerSketchPoint.geometry
    c = sk.sketchCurves.sketchCircles.addByCenterRadius(
        ctx.pt(rc.x + 0.004 * jitter, rc.y + 0.006 * jitter, 0), r_seed_cm)
    sk.geometricConstraints.addConcentric(ref_circle, c)
    d = sk.sketchDimensions.addDiameterDimension(
        c, ctx.pt(rc.x + r_seed_cm + 0.3, rc.y - 0.3, 0))
    d.parameter.expression = dia_expr
    return c


def loop_profiles(sk, loops):
    coll = adsk.core.ObjectCollection.create()
    n = 0
    for pr in sk.profiles:  # fusionhelper: allow R11 — collection add, not a document mutation
        if pr.profileLoops.count == loops:
            coll.add(pr)
            n += 1
    if n == 0:
        raise RuntimeError("%s: no profile with %d loops" % (sk.name, loops))
    return coll, n


def offset_plane_checked(ctx, base, expr, name, axis, want_cm):
    """Offset plane from base by expr; if the sketch origin lands on the
    wrong side of the axis, rebuild with the negated expression (R6: the
    mapping is read back, never assumed)."""
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


def run(_context: str):
    ctx = BuildCtx(adsk.core.Application.get())
    ensure_params(ctx)
    v = ctx.val
    shell = body_named(ctx, "shell")
    floor_plane = ctx.planes.itemByName("floor_plane")
    if floor_plane is None:
        raise RuntimeError("floor_plane missing")

    # ---- Brook standoffs ---------------------------------------------------
    if not feature_exists(ctx, "brook_standoffs"):
        sk = ctx.root.sketches.add(floor_plane)
        sk.name = "brook_standoffs"
        z = v("floor_t")
        px, py = v("brook_pitch_x") / 2, v("brook_pitch_y") / 2
        cx, cy = v("brook_cx"), v("brook_cy")
        k = 0
        for sx, sy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
            k += 1
            xe = "brook_cx %s brook_pitch_x / 2" % ("+" if sx > 0 else "-")
            ye = "brook_cy %s brook_pitch_y / 2" % ("+" if sy > 0 else "-")
            outer = ctx.bound_circle(
                sk, (cx + sx * px, cy + sy * py, z), v("so_od") / 2, "so_od",
                x_pos="abs(%s)" % xe, v_pos="abs(%s)" % ye)
            concentric_circle(ctx, sk, outer, v("so_pilot") / 2, "so_pilot", k)
            adsk.doEvents()
        if not sk.isFullyConstrained:
            raise RuntimeError("brook_standoffs sketch not fully constrained")
        profs, n = loop_profiles(sk, 2)
        if n != 4:
            raise RuntimeError("brook_standoffs expected 4 annuli, got %d" % n)
        v0 = shell.volume
        f = ctx.checked_join(profs, "so_h", shell, lambda b: b.volume - v0 > 0.5, "standoffs")
        f.name = "brook_standoffs"
        shell = body_named(ctx, "shell")
        print("brook standoffs: shell +%.2f cm3" % (shell.volume - v0))
    adsk.doEvents()

    # ---- LiPo tray -----------------------------------------------------------
    if not feature_exists(ctx, "lipo_tray_wall"):
        sk = ctx.root.sketches.add(floor_plane)
        sk.name = "lipo_tray_outer"
        ctx.bound_rect2(
            sk, (v("lipo_cx"), v("lipo_cy"), v("floor_t")),
            v("tray_out_w") / 2, v("tray_out_d") / 2,
            u_size="tray_out_w", v_size="tray_out_d",
            u_pos=("lipo_cx", "tray_out_w / 2"), v_pos=("lipo_cy", "tray_out_d / 2"))
        if not sk.isFullyConstrained:
            raise RuntimeError("lipo_tray_outer sketch not fully constrained")
        v0 = shell.volume
        f = ctx.checked_join(ctx.all_profiles(sk), "tray_h", shell,
                             lambda b: b.volume - v0 > 15.0, "tray_outer")
        f.name = "lipo_tray_wall"
        shell = body_named(ctx, "shell")
        v1 = shell.volume
        top = ctx.planes.itemByName("tray_top_plane")
        if top is None:
            top = ctx.plane_at_z("tray_top_z", "tray_top_plane")
        sk = ctx.root.sketches.add(top)
        sk.name = "lipo_tray_inner"
        ctx.bound_rect2(
            sk, (v("lipo_cx"), v("lipo_cy"), v("tray_top_z")),
            v("tray_in_w") / 2, v("tray_in_d") / 2,
            u_size="tray_in_w", v_size="tray_in_d",
            u_pos=("lipo_cx", "tray_in_w / 2"), v_pos=("lipo_cy", "tray_in_d / 2"))
        if not sk.isFullyConstrained:
            raise RuntimeError("lipo_tray_inner sketch not fully constrained")
        f = ctx.blind_cut(ctx.all_profiles(sk), "tray_h", [shell], "tray_pocket", min_vol_cm3=15.0)
        f.name = "lipo_tray_pocket"
        shell = body_named(ctx, "shell")
        print("lipo tray: wall +%.2f cm3, pocket -%.2f cm3" % (v1 - v0, v1 - shell.volume))
    adsk.doEvents()

    # ---- coil boss on the underside -----------------------------------------
    if not feature_exists(ctx, "coil_boss"):
        sk = ctx.root.sketches.add(ctx.root.xYConstructionPlane)
        sk.name = "coil_boss"
        ctx.bound_circle(
            sk, (v("coil_x"), v("coil_y"), 0), v("coil_boss_d") / 2, "coil_boss_d",
            x_pos="abs(coil_x)", v_pos="abs(coil_y)")
        if not sk.isFullyConstrained:
            raise RuntimeError("coil_boss sketch not fully constrained")
        v0 = shell.volume
        want = 3.14159 * (v("coil_boss_d") / 2) ** 2 * v("coil_boss_h")
        f = ctx.checked_join(ctx.all_profiles(sk), "coil_boss_h", shell,
                             lambda b: abs((b.volume - v0) - want) < 0.05 * want, "coil_boss")
        f.name = "coil_boss"
        shell = body_named(ctx, "shell")
        print("coil boss: shell +%.2f cm3 (want %.2f), min z %.2f mm" % (
            shell.volume - v0, want, shell.boundingBox.minPoint.z * 10))
    adsk.doEvents()

    # ---- antenna bracket --------------------------------------------------
    if not feature_exists(ctx, "antenna_bracket"):
        sk = ctx.root.sketches.add(floor_plane)
        sk.name = "antenna_bracket"
        ctx.bound_rect2(
            sk, (v("ant_x"), v("ant_cy"), v("floor_t")),
            v("ant_t") / 2, v("ant_len") / 2,
            u_size="ant_t", v_size="ant_len",
            u_pos=("ant_x", "ant_t / 2"), v_pos=("ant_cy", "ant_len / 2"))
        if not sk.isFullyConstrained:
            raise RuntimeError("antenna_bracket sketch not fully constrained")
        v0 = shell.volume
        f = ctx.checked_join(ctx.all_profiles(sk), "ant_h", shell,
                             lambda b: b.volume - v0 > 0.5, "bracket")
        f.name = "antenna_bracket"
        shell = body_named(ctx, "shell")
        v1 = shell.volume
        # clearance hole along x, sketched on a YZ-offset plane at ant_x
        pl = offset_plane_checked(ctx, ctx.root.yZConstructionPlane, "ant_x",
                                  "antenna_plane", 0, v("ant_x"))
        sk = ctx.root.sketches.add(pl)
        sk.name = "antenna_hole"
        ctx.U = (0.0, 1.0, 0.0)
        ctx.bound_circle(
            sk, (v("ant_x"), v("ant_cy"), v("ant_hole_z")), v("ant_hole") / 2, "ant_hole",
            x_pos="abs(ant_cy)", v_pos="ant_hole_z")
        ctx.U = (1.0, 0.0, 0.0)
        if not sk.isFullyConstrained:
            raise RuntimeError("antenna_hole sketch not fully constrained")
        f = ctx.sym_cut(ctx.all_profiles(sk), "ant_t * 3", [shell], min_vol_cm3=0.02)
        f.name = "antenna_hole"
        shell = body_named(ctx, "shell")
        print("antenna bracket: +%.2f cm3, hole -%.3f cm3" % (v1 - v0, v1 - shell.volume))
    adsk.doEvents()

    # ---- port window through the facet wall ----------------------------------
    if not feature_exists(ctx, "port_window"):
        pl = offset_plane_checked(ctx, ctx.root.xZConstructionPlane, "facet_y",
                                  "facet_plane", 1, v("facet_y"))
        sk = ctx.root.sketches.add(pl)
        sk.name = "port_window"
        ctx.V = (0.0, 0.0, 1.0)
        ctx.bound_rect2(
            sk, (0, v("facet_y"), v("port_cz")),
            v("port_w") / 2, v("port_h") / 2,
            u_size="port_w", v_size="port_h",
            u_pos=("0 mm", "port_w / 2"), v_pos=("port_cz", "port_h / 2"))
        ctx.V = (0.0, 1.0, 0.0)
        if not sk.isFullyConstrained:
            raise RuntimeError("port_window sketch not fully constrained")
        v0 = shell.volume
        f = ctx.blind_cut(ctx.all_profiles(sk), "boss_in + 2 mm", [shell], "window", min_vol_cm3=3.0)
        f.name = "port_window"
        shell = body_named(ctx, "shell")
        print("port window: -%.2f cm3" % (v0 - shell.volume))
    adsk.doEvents()

    # ---- TPU ring, separate body ---------------------------------------------
    if not body_exists(ctx, "tpu_ring"):
        pl = ctx.planes.itemByName("ring_plane")
        if pl is None:
            pl = ctx.plane_at_z("-ring_t", "ring_plane")
        sk = ctx.root.sketches.add(pl)
        sk.name = "tpu_ring"
        outer = centred_circle(ctx, sk, v("ring_od") / 2, "ring_od", 1)
        concentric_circle(ctx, sk, outer, v("ring_id") / 2, "ring_id", 2)
        ctx.bound_circle(
            sk, (v("coil_x"), v("coil_y"), -v("ring_t")), v("ring_coil_hole") / 2, "ring_coil_hole",
            x_pos="abs(coil_x)", v_pos="abs(coil_y)")
        if not sk.isFullyConstrained:
            raise RuntimeError("tpu_ring sketch not fully constrained")
        profs, n = loop_profiles(sk, 3)
        if n != 1:
            raise RuntimeError("tpu_ring expected one 3-loop profile, got %d" % n)
        f, ring = ctx.checked_newbody(
            profs, "ring_t",
            lambda b: abs(b.boundingBox.maxPoint.z) < 0.01 and abs(b.boundingBox.minPoint.z + v("ring_t")) < 0.01,
            "ring")
        f.name = "tpu_ring"
        ring.name = "tpu_ring"
        print("tpu ring: %.2f cm3, z %.1f..%.1f" % (ring.volume, ring.boundingBox.minPoint.z * 10, ring.boundingBox.maxPoint.z * 10))
    adsk.doEvents()

    # ---- TPU tyre, separate body ---------------------------------------------
    if not body_exists(ctx, "tpu_tyre"):
        pl = ctx.planes.itemByName("tyre_plane")
        if pl is None:
            pl = ctx.plane_at_z("tyre_z0", "tyre_plane")
        sk = ctx.root.sketches.add(pl)
        sk.name = "tpu_tyre"
        outer = centred_circle(ctx, sk, v("tyre_od") / 2, "tyre_od", 1)
        concentric_circle(ctx, sk, outer, v("shell_dia") / 2, "shell_dia", 2)
        if not sk.isFullyConstrained:
            raise RuntimeError("tpu_tyre sketch not fully constrained")
        profs, n = loop_profiles(sk, 2)
        top_want = v("ridge_hi_z")
        f, tyre = ctx.checked_newbody(
            profs, "tyre_h",
            lambda b: abs(b.boundingBox.maxPoint.z - top_want) < 0.01,
            "tyre")
        f.name = "tpu_tyre"
        tyre.name = "tpu_tyre"
        print("tpu tyre: %.2f cm3, z %.1f..%.1f" % (tyre.volume, tyre.boundingBox.minPoint.z * 10, tyre.boundingBox.maxPoint.z * 10))
    adsk.doEvents()

    # ---- pitch liveness, read back from the standoff axes ---------------------
    def standoff_dx():
        sh = body_named(ctx, "shell")
        cx, cy = v("brook_cx"), v("brook_cy")
        xs = []
        for face in sh.faces:
            cyl = adsk.core.Cylinder.cast(face.geometry)
            if cyl is None or abs(cyl.radius - v("so_od") / 2) > 0.005:
                continue
            o = cyl.origin
            if abs(o.y - cy) < v("brook_pitch_y") and face.boundingBox.maxPoint.z < v("floor_t") + v("so_h") + 0.01:
                xs.append(abs(o.x - cx) * 10)
        return sorted(set(round(x, 2) for x in xs))

    d0 = standoff_dx()
    if len(d0) != 1 or abs(d0[0] - v("brook_pitch_x") * 5) > 0.01:
        raise RuntimeError("standoff half-pitch read %s, wanted %.2f" % (d0, v("brook_pitch_x") * 5))
    ctx.up.itemByName("brook_pitch_x").expression = "90 mm"
    adsk.doEvents()
    d1 = standoff_dx()
    ctx.up.itemByName("brook_pitch_x").expression = "88 mm"
    adsk.doEvents()
    d2 = standoff_dx()
    if d1 != [45.0] or d2 != [44.0]:
        raise RuntimeError("brook_pitch_x not live: %s -> %s -> %s" % (d0, d1, d2))
    print("brook_pitch_x live: standoff half-pitch %.1f -> %.1f -> %.1f mm" % (d0[0], d1[0], d2[0]))

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
