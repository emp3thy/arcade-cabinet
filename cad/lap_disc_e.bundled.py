"""Lap pad, D-014: the nested disc. Stage E -- the tyre meets the port facet,
in the document that holds stages A to D.

The stage B facet cuts a flat facet_w wide across the rear wall at facet_y,
full height. The wall's outer radius is shell_dia / 2, so between the flat
and the tyre's round inner face there was a lens-shaped gap, shell_dia / 2 -
facet_y (3.8 mm) wide at x = 0, open from the floor to the rim slope: the
"hole" seen from above on 2026-09-13. The port behind the facet is the
charging input, so it must stay reachable from outside (owner, same day).
Two features on the tpu_tyre body:

  tyre_fill    JOIN the lens between the facet chord and the shell circle,
               tyre_z0 to ridge_hi_z (the tyre's own height). Profile: the
               piece of a rectangle (facet_w + 16 mm wide, from facet_y
               outward past the circle) that lies inside a shell_dia circle,
               picked by centroid and area, not by index (R4). No new root:
               the arc bounds it whatever the rectangle's depth.
  tyre_window  CUT a tyre_win_w x tyre_win_h window through the filled tyre
               from the facet plane outward, in line with the stage C
               port_window (centre x = 0, z = port_cz). tyre_win_clear a
               side over the port window. TPU bridges above and below the
               window are about 3 mm; the tyre is a stretched O-ring, so
               they carry tension.

Oracles: tyre_fill adds exactly the segment area (R^2 (t - sin t cos t),
t = acos(facet_y / R)) times tyre_h; tyre_window removes the integral of
(sqrt(Ro^2 - x^2) - facet_y) over the window width, times its height, LESS
the material the stage D tyre_r fillets had already taken off the outer
corners inside the window's height (attempt 1 measured the cut 2.6 % short
of the plain prism: the window's top and bottom edges sit inside the
fillet zones). The window feature is rebuilt on every run so the oracle
always sees the cut it checks.

Still not modelled: port-board M3 holes (ASSUMED 24 x 20), rim-band
lettering, raised-disc colour split. Open: an external charging port
contradicts D-010 / D-014 (Qi only, no reachable USB-C) -- decision log
entry needed, owner's call.
"""
FH_ATTEMPT = 2
FH_OPTS = {
    "only_params": ["tyre_win_clear"],
    "liveness_budget_s": 120,
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

PARAMS_E = (
    ("tyre_win_clear", "0.5 mm", "mm", "tyre window clearance a side over the port window"),
    ("tyre_win_w", "port_w + 2 * tyre_win_clear", "mm", "derived"),
    ("tyre_win_h", "port_h + 2 * tyre_win_clear", "mm", "derived"),
    ("fill_depth", "shell_dia / 2 - facet_y + 5 mm", "mm", "derived: fill rectangle from the facet past the shell circle"),
    ("fill_w", "facet_w + 16 mm", "mm", "derived: fill rectangle wider than the facet chord"),
)

NEEDED = ("shell_dia", "facet_w", "facet_y", "tyre_z0", "tyre_h", "ridge_hi_z",
          "tyre_od", "tyre_r", "port_w", "port_h", "port_cz")


def ensure_params(ctx):
    for name in NEEDED:
        if ctx.up.itemByName(name) is None:
            raise RuntimeError("parameter %s missing: run stages A to D first" % name)
    for name, expr, unit, comment in PARAMS_E:
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


def centred_circle(ctx, sk, r_seed_cm, dia_expr, jitter):
    c = sk.sketchCurves.sketchCircles.addByCenterRadius(
        ctx.pt(0.011 + 0.003 * jitter, 0.017 + 0.005 * jitter, 0), r_seed_cm)
    sk.geometricConstraints.addCoincident(c.centerSketchPoint, sk.originPoint)
    d = sk.sketchDimensions.addDiameterDimension(c, ctx.pt(r_seed_cm + 0.4, -0.4, 0))
    d.parameter.expression = dia_expr
    return c


def segment_profile(sk, facet_y_cm, max_area_cm2):
    """The one profile whose centroid lies beyond the facet chord and whose
    area is small: the circle segment, not the rectangle's outer remainder
    and not the rest of the disc (R4: predicate, not index)."""
    coll = adsk.core.ObjectCollection.create()
    found = []
    for pr in sk.profiles:  # fusionhelper: allow R11 — collection add, not a document mutation
        props = pr.areaProperties(adsk.fusion.CalculationAccuracy.HighCalculationAccuracy)
        c = sk.sketchToModelSpace(props.centroid)
        found.append((round(props.area, 3), round(c.y * 10, 2)))
        if c.y > facet_y_cm and props.area < max_area_cm2:
            coll.add(pr)
    if coll.count != 1:
        raise RuntimeError("segment profile: want 1, matched %d; profiles (area cm2, centroid y mm): %s"
                           % (coll.count, found))
    return coll


def segment_area_cm2(R, d):
    t = math.acos(d / R)
    return R * R * (t - math.sin(t) * math.cos(t))


def window_volume_cm3(Ro, d, half_w, h, n=400):
    """Integral of (sqrt(Ro^2 - x^2) - d) dx over [-half_w, half_w], times h."""
    s = 0.0
    dx = 2 * half_w / n
    for i in range(n):
        x = -half_w + (i + 0.5) * dx
        s += math.sqrt(Ro * Ro - x * x) - d
    return s * dx * h


def fillet_deficit_cm3(r_f, gap, Ro, half_w):
    """Material a radius-r_f round on the tyre's outer edge had already
    removed within the window: the corner strip from the window's edge
    (gap from the tyre's edge) to the tyre's edge, integrated over the
    arc the window spans at Ro. Zero when the window clears the fillet."""
    u1 = max(0.0, min(r_f, r_f - gap))
    if u1 <= 0:
        return 0.0
    area = r_f * u1 - (u1 / 2 * math.sqrt(r_f * r_f - u1 * u1) + r_f * r_f / 2 * math.asin(u1 / r_f))
    arc = 2 * Ro * math.asin(half_w / Ro)
    return area * arc


def run(_context: str):
    ctx = BuildCtx(adsk.core.Application.get())
    ensure_params(ctx)
    v = ctx.val
    tyre = body_named(ctx, "tpu_tyre")
    R = v("shell_dia") / 2
    d = v("facet_y")

    # ---- tyre fill: the lens between the facet chord and the shell circle ----
    if not feature_exists(ctx, "tyre_fill"):
        pl = ctx.planes.itemByName("tyre_plane")
        if pl is None:
            raise RuntimeError("tyre_plane missing")
        sk = ctx.root.sketches.add(pl)
        sk.name = "tyre_fill"
        centred_circle(ctx, sk, R, "shell_dia", 1)
        fd = v("fill_depth")
        ctx.bound_rect2(
            sk, (0, d + fd / 2, v("tyre_z0")),
            v("fill_w") / 2, fd / 2,
            u_size="fill_w", v_size="fill_depth",
            u_pos=("0 mm", "fill_w / 2"), v_pos=("facet_y + fill_depth / 2", "fill_depth / 2"))
        if not sk.isFullyConstrained:
            raise RuntimeError("tyre_fill sketch not fully constrained")
        want = segment_area_cm2(R, d) * v("tyre_h")
        profs = segment_profile(sk, d, 3.0)
        v0 = tyre.volume
        f = ctx.checked_join(profs, "tyre_h", tyre,
                             lambda b: abs((b.volume - v0) - want) < 0.02 * want, "fill")
        f.name = "tyre_fill"
        tyre = body_named(ctx, "tpu_tyre")
        bb = tyre.boundingBox
        if abs(bb.minPoint.z - v("tyre_z0")) > 0.01 or abs(bb.maxPoint.z - v("ridge_hi_z")) > 0.01:
            raise RuntimeError("tyre_fill changed the tyre's z range: %.2f..%.2f" % (bb.minPoint.z, bb.maxPoint.z))
        print("tyre fill: +%.4f cm3 (want %.4f), tyre z %.1f..%.1f mm" % (
            tyre.volume - v0, want, bb.minPoint.z * 10, bb.maxPoint.z * 10))
    adsk.doEvents()

    # ---- tyre window, in line with the port window ----------------------------
    # Rebuilt every run: attempt 1 left a window whose oracle was wrong, and
    # the only way to re-check a cut's volume is to make it again.
    old = ctx.extrudes.itemByName("tyre_window")
    if old is not None:
        old.deleteMe()
        adsk.doEvents()
    old_sk = ctx.root.sketches.itemByName("tyre_window")
    if old_sk is not None:
        old_sk.deleteMe()
        adsk.doEvents()
    tyre = body_named(ctx, "tpu_tyre")
    if True:
        pl = ctx.planes.itemByName("facet_plane")
        if pl is None:
            raise RuntimeError("facet_plane missing")
        sk = ctx.root.sketches.add(pl)
        sk.name = "tyre_window"
        ctx.V = (0.0, 0.0, 1.0)
        ctx.bound_rect2(
            sk, (0, d, v("port_cz")),
            v("tyre_win_w") / 2, v("tyre_win_h") / 2,
            u_size="tyre_win_w", v_size="tyre_win_h",
            u_pos=("0 mm", "tyre_win_w / 2"), v_pos=("port_cz", "tyre_win_h / 2"))
        ctx.V = (0.0, 1.0, 0.0)
        if not sk.isFullyConstrained:
            raise RuntimeError("tyre_window sketch not fully constrained")
        Ro, hw = v("tyre_od") / 2, v("tyre_win_w") / 2
        z_lo, z_hi = v("port_cz") - v("tyre_win_h") / 2, v("port_cz") + v("tyre_win_h") / 2
        want = (window_volume_cm3(Ro, d, hw, v("tyre_win_h"))
                - fillet_deficit_cm3(v("tyre_r"), z_lo - v("tyre_z0"), Ro, hw)
                - fillet_deficit_cm3(v("tyre_r"), v("ridge_hi_z") - z_hi, Ro, hw))
        v0 = tyre.volume
        f = ctx.blind_cut(ctx.all_profiles(sk), "tyre_od / 2 - facet_y + 2 mm", [tyre],
                          "tyre_win", min_vol_cm3=0.5 * want)
        f.name = "tyre_window"
        tyre = body_named(ctx, "tpu_tyre")
        removed = v0 - tyre.volume
        if abs(removed - want) > 0.02 * want:
            raise RuntimeError("tyre_window removed %.4f cm3, wanted %.4f" % (removed, want))
        print("tyre window: -%.4f cm3 (want %.4f)" % (removed, want))
    adsk.doEvents()

    # ---- read-back: the lens is closed where the tyre stands ------------------
    P = adsk.core.Point3D.create
    inside = adsk.fusion.PointContainment.PointInsidePointContainment
    y_mid = (d + R) / 2
    z_mid = (v("tyre_z0") + v("ridge_hi_z")) / 2
    if tyre.pointContainment(P(2.5, y_mid, z_mid)) != inside:
        raise RuntimeError("lens at x=25 mm still open inside the tyre")
    if tyre.pointContainment(P(0, y_mid, v("port_cz"))) == inside:
        raise RuntimeError("tyre window did not open the port line")
    print("lens closed at x=25 mm, open on the port axis at z=%.1f mm" % (v("port_cz") * 10))

    tl = ctx.des.timeline
    bad = []
    for i in range(tl.count):
        feat = adsk.fusion.Feature.cast(tl.item(i).entity)
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
