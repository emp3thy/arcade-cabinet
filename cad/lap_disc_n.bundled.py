"""Lap pad, D-014: the nested disc. Stage N -- anti-slide grooves in the TPU
ring's underside (2026-09-13), in the document that holds stages A to M.

D-014 put the wedge's anti-slide job on the TPU ring's friction and left the
underside flat: one planar face, 486.2 cm2, at z -6. A 2.2 kg pad over that
area presses at about 0.44 kPa, which is too little to push 85A TPU into a
denim weave or a beanbag's pile, so the pad grips by adhesion alone.

  tpu_grooves   N_GROOVE concentric grooves cut groove_d into the underside,
                groove_w wide, groove_pitch apart, innermost centred at
                groove_r0.

Cutting grooves rather than standing ridges proud keeps the pad's z envelope
exactly as D-016 left it (-6 to 0), keeps the bolt clamp faces flat, and
leaves the same first layer to print against the bed.

What this buys: the lands between the grooves carry the same weight over
about 291 cm2 instead of 486, so the contact pressure rises by about 1.67x
and the TPU conforms further into a soft surface. [UNVERIFIED] -- friction
judgement, not measured. It is the right direction for a lap and the wrong
one for a hard smooth surface, where rubber friction follows real contact
area and a flat pad wins; the lap is the design case.

Concentric, not a crosshatch: concentric rings resist the fore-and-aft slide
that a rounded thigh causes, and leave rotation free, which D-014 wants --
each player takes their own hand angle by turning the pad.

Depth is deliberately shallow. The pressure concentration that makes a groove
grip is the same thing that imprints on a thigh over a long session, so this
is 1 mm, not the 3 mm ridges D-013 drew for the superseded wedge.

Radii are boxed in at both ends. The grooves must clear the inner TPU bolt
counterbores (in_rc 62, cb_d 7, so they reach r 65.5) and the base bolt
counterbores (base_rc 132.1, reaching r 128.6), and must stay inside the
ring's own filleted edges. The band left is r 67 to r 127.1, and eight
grooves at an 8 mm pitch span exactly 60 of its 60.1 mm. The script asserts
every one of those clearances before it cuts.

Print orientation is unchanged: the TPU ring prints counterbore side down, so
the grooves are recesses in the first layer -- no overhang, no support. Print
that face against a textured plate: TPU off smooth PEI comes out glossy, and
that costs more grip than these grooves buy back.

Oracles: the cut is checked against the summed annulus areas times the depth;
then the underside's remaining flat is read back as the horizontal faces at
z -ring_t, whose area must have dropped by exactly the grooves' plan area,
the groove floors are read back at z -ring_t + groove_d, and point
containment is probed in every groove and on every land between them.
"""
FH_ATTEMPT = 1
FH_OPTS = {
    "only_params": ["groove_w", "groove_d", "groove_pitch", "groove_r0"],
    "liveness_budget_s": 240,
    "max_bodies": 6,
    # The stage M art sketches fail the constraints check by design, which
    # would otherwise skip liveness here as prior_failure.
    "force_liveness": True,
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

PARAMS_N = (
    ("groove_w",     "4 mm",  "mm", "anti-slide groove width in the TPU ring's underside"),
    ("groove_d",     "1 mm",  "mm", "anti-slide groove depth from the underside"),
    ("groove_pitch", "8 mm",  "mm", "centre-to-centre spacing of the grooves"),
    ("groove_r0",    "69 mm", "mm", "radius of the innermost groove's centreline"),
)
NEEDED = ("ring_t", "ring_id", "ring_od", "ring_r", "cb_d", "base_rc", "in_rc")
N_GROOVE = 8
PI = math.pi
EPS = 0.02        # cm, containment probes
FACE_EPS = 0.002  # cm, face height coincidence
CLEAR = 0.15      # cm, wanted clearance from a groove edge to a counterbore
N_PROBE = 8       # angles probed per groove and per land


def ensure_params(ctx):
    for name in NEEDED:
        if ctx.up.itemByName(name) is None:
            raise RuntimeError("parameter %s missing: run stages A to M first" % name)
    for name, expr, unit, comment in PARAMS_N:
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


def groove_radii(ctx):
    """Centreline radius of each groove, in cm, innermost first."""
    return [ctx.val("groove_r0") + k * ctx.val("groove_pitch")
            for k in range(N_GROOVE)]


def land_radii(ctx):
    """Mid-radius of each land between two grooves, in cm."""
    rs = groove_radii(ctx)
    return [(a + b) / 2.0 for a, b in zip(rs, rs[1:])]


def check_band(ctx):
    """Everything the groove band has to miss, asserted before anything is cut."""
    v = ctx.val
    rs = groove_radii(ctx)
    inner = rs[0] - v("groove_w") / 2.0
    outer = rs[-1] + v("groove_w") / 2.0
    in_cb = v("in_rc") + v("cb_d") / 2.0
    base_cb = v("base_rc") - v("cb_d") / 2.0
    if inner < in_cb + CLEAR:
        raise RuntimeError("innermost groove reaches r %.2f mm, the inner bolt "
                           "counterbores reach r %.2f" % (inner * 10, in_cb * 10))
    if outer > base_cb - CLEAR:
        raise RuntimeError("outermost groove reaches r %.2f mm, the base bolt "
                           "counterbores start at r %.2f" % (outer * 10, base_cb * 10))
    if inner < v("ring_id") / 2.0 + v("ring_r"):
        raise RuntimeError("innermost groove at r %.2f mm runs into the ring's "
                           "inner edge fillet" % (inner * 10))
    if outer > v("ring_od") / 2.0 - v("ring_r"):
        raise RuntimeError("outermost groove at r %.2f mm runs into the ring's "
                           "outer edge fillet" % (outer * 10))
    if v("groove_d") >= v("ring_t") / 2.0:
        raise RuntimeError("groove_d %.2f mm is half the ring's %.2f mm thickness"
                           % (v("groove_d") * 10, v("ring_t") * 10))
    print("groove band r %.1f..%.1f mm: %.1f mm clear of the inner counterbores, "
          "%.1f mm of the base ones" % (inner * 10, outer * 10,
                                        (inner - in_cb) * 10, (base_cb - outer) * 10))


def concentric_circle(ctx, sk, r_cm, dia_expr, jitter):
    """A circle on the sketch origin, held there by a coincident constraint
    rather than by a pair of 0 mm dimensions, so the only dimension on it is
    the one that does work. Created off-centre: coincident-coordinate circles
    trigger silent alignment inference and later over-constrain; the
    constraint snaps it home."""
    c = sk.sketchCurves.sketchCircles.addByCenterRadius(
        ctx.pt(0.011 + 0.003 * jitter, 0.017 + 0.005 * jitter, 0.0), r_cm)
    sk.geometricConstraints.addCoincident(c.centerSketchPoint, sk.originPoint)
    d = sk.sketchDimensions.addDiameterDimension(
        c, ctx.pt(r_cm + 0.4, -0.4, 0.0))
    d.parameter.expression = dia_expr
    return c


def draw_grooves(ctx, sk):
    """Two concentric circles per groove, each held on the origin and
    dimensioned by diameter. The radii are expressions, not numbers, so the
    whole band moves with groove_r0, groove_pitch and groove_w."""
    j = 0
    for k, rc in enumerate(groove_radii(ctx)):
        for sign, tag in ((-1.0, "-"), (1.0, "+")):
            j += 1
            expr = ("2 * ( groove_r0 + %d * groove_pitch %s groove_w / 2 )"
                    % (k, tag))
            concentric_circle(ctx, sk, rc + sign * ctx.val("groove_w") / 2.0, expr, j)
            adsk.doEvents()
    if not sk.isFullyConstrained:
        raise RuntimeError("%s sketch not fully constrained" % sk.name)


def groove_profiles(ctx, sk):
    """The annulus of each groove, picked by its outer radius. A land between
    two grooves has a different outer radius (groove_pitch - groove_w/2
    further out), so the two never collide."""
    want = [r + ctx.val("groove_w") / 2.0 for r in groove_radii(ctx)]
    coll = adsk.core.ObjectCollection.create()
    hit = []
    for pr in sk.profiles:  # fusionhelper: allow R11 -- collection add, not a document mutation
        bb = pr.boundingBox
        r_out = max(abs(bb.minPoint.x), abs(bb.maxPoint.x),
                    abs(bb.minPoint.y), abs(bb.maxPoint.y))
        for r in want:  # fusionhelper: allow R11 -- collection add, not a document mutation
            if abs(r_out - r) < 0.02 and r not in hit:
                coll.add(pr)
                hit.append(r)
                break
    if len(hit) != N_GROOVE:
        raise RuntimeError("picked %d groove profiles of %d (sketch has %d)"
                           % (len(hit), N_GROOVE, sk.profiles.count))
    return coll


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


def flat_area_at(body, z_cm):
    """Total area of the horizontal planar faces lying at z_cm. Sign of the
    face normal is not a filter -- measured 2026-09-13, Fusion hands back a
    recess floor with normal.z -1 and the surface it was cut into with +1."""
    total = 0.0
    n = 0
    for f in body.faces:
        pl = adsk.core.Plane.cast(f.geometry)
        if pl is None or abs(pl.normal.z) < 0.999:
            continue
        bb = f.boundingBox
        if abs(bb.maxPoint.z - z_cm) > FACE_EPS or abs(bb.minPoint.z - z_cm) > FACE_EPS:
            continue
        total += f.area
        n += 1
    return total, n


def plan_area(ctx):
    """Summed plan area of the grooves: 2 pi r w for each."""
    return sum(2.0 * PI * r * ctx.val("groove_w") for r in groove_radii(ctx))


def read_back(ctx, contact_before):
    v = ctx.val
    tpu = body_named(ctx, "tpu_ring")
    P = ctx.pt
    inside = adsk.fusion.PointContainment.PointInsidePointContainment
    z_under = -v("ring_t")
    z_floor = z_under + v("groove_d")
    want = plan_area(ctx)

    contact, nf = flat_area_at(tpu, z_under)
    lost = contact_before - contact
    if abs(lost - want) > 0.02 * want:
        raise RuntimeError("underside lost %.2f cm2 of contact, wanted %.2f"
                           % (lost, want))
    print("contact %.1f -> %.1f cm2 over %d faces; %.1f cm2 given to the grooves"
          % (contact_before, contact, nf, lost))

    floors, nf = flat_area_at(tpu, z_floor)
    if abs(floors - want) > 0.02 * want:
        raise RuntimeError("groove floors are %.2f cm2 over %d faces, wanted %.2f"
                           % (floors, nf, want))
    print("groove floors %.2f cm2 at z %.2f mm over %d faces" % (floors, z_floor * 10, nf))

    z_probe = z_under + v("groove_d") / 2.0
    for r in groove_radii(ctx):
        for i in range(N_PROBE):
            t = 2.0 * PI * i / N_PROBE
            if tpu.pointContainment(P(r * math.cos(t), r * math.sin(t), z_probe)) == inside:
                raise RuntimeError("groove at r %.1f mm is solid at %.0f deg"
                                   % (r * 10, math.degrees(t)))
    for r in land_radii(ctx):
        for i in range(N_PROBE):
            t = 2.0 * PI * i / N_PROBE
            if tpu.pointContainment(P(r * math.cos(t), r * math.sin(t), z_probe)) != inside:
                raise RuntimeError("land at r %.1f mm is open at %.0f deg"
                                   % (r * 10, math.degrees(t)))
    print("%d grooves open and %d lands solid, %d angles each"
          % (N_GROOVE, len(land_radii(ctx)), N_PROBE))

    bb = tpu.boundingBox
    if abs(bb.minPoint.z - z_under) > FACE_EPS or abs(bb.maxPoint.z) > FACE_EPS:
        raise RuntimeError("the TPU ring's z envelope moved: %.2f..%.2f mm"
                           % (bb.minPoint.z * 10, bb.maxPoint.z * 10))
    print("z envelope unchanged at %.1f..%.1f mm" % (bb.minPoint.z * 10, bb.maxPoint.z * 10))


def run(_context: str):
    app = adsk.core.Application.get()
    if not app.activeDocument.name.startswith("Arcade Controller"):
        raise RuntimeError("wrong document " + app.activeDocument.name)
    ctx = BuildCtx(app)
    ensure_params(ctx)
    healthy = adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState
    check_band(ctx)

    ring_plane = ctx.planes.itemByName("ring_plane")
    if ring_plane is None:
        raise RuntimeError("ring_plane missing: run stages A to M first")

    z_under = -ctx.val("ring_t")
    if feature_exists(ctx, "tpu_grooves_cut"):
        # Already cut: the contact face is the post-cut one, so the oracle is
        # rebuilt from the grooves' own plan area rather than a before reading.
        contact_before = flat_area_at(body_named(ctx, "tpu_ring"), z_under)[0] + plan_area(ctx)
        print("stage N already built; verifying in place")
    else:
        contact_before = flat_area_at(body_named(ctx, "tpu_ring"), z_under)[0]
        sk = ctx.root.sketches.add(ring_plane)
        sk.name = "tpu_grooves"
        draw_grooves(ctx, sk)
        want = plan_area(ctx) * ctx.val("groove_d")
        f, removed = cut_named(ctx, groove_profiles(ctx, sk), "groove_d",
                               "tpu_ring", want, 0.02, "tpu_grooves")
        # Suffixed: sketches and features share one name namespace, and a
        # feature named after its own sketch is silently renamed "name (1)",
        # which then slips past an itemByName guard.
        f.name = "tpu_grooves_cut"
        print("tpu_grooves: -%.4f cm3 over %.2f cm2 (want %.4f)"
              % (removed, plan_area(ctx), want))
    adsk.doEvents()

    read_back(ctx, contact_before)

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
