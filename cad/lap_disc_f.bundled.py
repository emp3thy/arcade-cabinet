"""Lap pad, D-014: the nested disc. Stage F -- D-015 cleanup, in the document
that holds stages A to E. The Qi receiver is gone (D-015, 2026-09-13), so:

  coil boss     the stage C coil_boss join on the shell's underside and its
                sketch are deleted. Oracle: the shell loses exactly
                pi (coil_boss_d / 2)^2 coil_boss_h and its underside returns
                to z = 0.
  tpu ring      the stage C ring carried a ring_coil_hole over the boss. The
                stage D ring_round fillet, the ring extrude and its sketch are
                deleted and the ring is rebuilt from ring_od / ring_id alone,
                then rounded again with ring_r (same predicate-picked edges and
                Pappus oracle as stage D). Oracle: annulus volume less the two
                rounds.
  parameters    coil_x, coil_y, coil_boss_d, coil_boss_h, ring_coil_hole are
                deleted once nothing references them.

Fusion's active document may be another session's when this runs (two
sessions share one Fusion, 2026-09-13): the script finds the lap pad document
by name and activates it before touching anything.
"""
FH_ATTEMPT = 1
FH_OPTS = {
    "only_params": ["ring_od", "ring_id", "ring_t", "ring_r"],
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

DOC_PREFIX = "Arcade Controller"
DEAD_PARAMS = ("ring_coil_hole", "coil_boss_d", "coil_boss_h", "coil_x", "coil_y")
NEEDED = ("ring_od", "ring_id", "ring_t", "ring_r", "floor_t")
PI = math.pi
CORNER_AREA = 1.0 - PI / 4.0
CORNER_CENTROID = 0.2234


def activate_lap_pad(app):
    doc = app.activeDocument
    if doc is not None and doc.name.startswith(DOC_PREFIX):
        return doc
    for i in range(app.documents.count):
        d = app.documents.item(i)
        if d.name.startswith(DOC_PREFIX):
            d.activate()
            adsk.doEvents()
            return d
    raise RuntimeError("no open document named %s*" % DOC_PREFIX)


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


def delete_extrude(ctx, name):
    """Delete an extrude by either spelling of its name, then its sketch."""
    for n in (name, name + " (1)"):
        f = ctx.extrudes.itemByName(n)
        if f is not None:
            f.deleteMe()
            adsk.doEvents()
    sk = ctx.root.sketches.itemByName(name)
    if sk is not None:
        sk.deleteMe()
        adsk.doEvents()


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


def circle_edges(body, wants, tol=0.005):
    coll = adsk.core.ObjectCollection.create()
    seen = []
    hits = [0] * len(wants)
    for e in body.edges:  # fusionhelper: allow R11 — collection add, not a document mutation
        circ = adsk.core.Circle3D.cast(e.geometry)
        if circ is None:
            continue
        c = circ.center
        seen.append((round(c.x * 10, 1), round(c.y * 10, 1), round(circ.radius * 10, 2), round(c.z * 10, 2)))
        for i, (cx, cy, r, z) in enumerate(wants):  # fusionhelper: allow R11 — collection add, not a document mutation
            if (abs(c.x - cx) < tol and abs(c.y - cy) < tol
                    and abs(circ.radius - r) < tol and abs(c.z - z) < tol):
                coll.add(e)
                hits[i] += 1
    if any(h != 1 for h in hits):
        raise RuntimeError("edge match counts %s; circles on %s: %s" % (hits, body.name, sorted(set(seen))))
    return coll


def corner_volume(R, r, outer):
    rc = R - CORNER_CENTROID * r if outer else R + CORNER_CENTROID * r
    return 2.0 * PI * rc * r * r * CORNER_AREA


def rounded(ctx, name, body_name, edges, radius_param, want_cm3, tol=0.03):
    body = body_named(ctx, body_name)
    before = body.volume
    fillets = ctx.root.features.filletFeatures
    fin = fillets.createInput()
    fin.edgeSetInputs.addConstantRadiusEdgeSet(edges, ctx.cbs(radius_param), True)
    f = fillets.add(fin)
    adsk.doEvents()
    healthy = adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState
    body = body_named(ctx, body_name)
    removed = before - body.volume
    if f.healthState != healthy:
        f.deleteMe()
        raise RuntimeError("%s: fillet unhealthy (state %s)" % (name, f.healthState))
    if abs(removed - want_cm3) > tol * want_cm3:
        f.deleteMe()
        raise RuntimeError("%s: removed %.4f cm3, wanted %.4f" % (name, removed, want_cm3))
    f.name = name
    print("%s: -%.4f cm3 (want %.4f)" % (name, removed, want_cm3))
    return f


def run(_context: str):
    app = adsk.core.Application.get()
    doc = activate_lap_pad(app)
    print("document:", doc.name)
    ctx = BuildCtx(app)
    v = ctx.val
    for name in NEEDED:
        if ctx.up.itemByName(name) is None:
            raise RuntimeError("parameter %s missing" % name)

    # ---- coil boss off the shell ------------------------------------------------
    shell = body_named(ctx, "shell")
    if ctx.extrudes.itemByName("coil_boss (1)") is not None or ctx.extrudes.itemByName("coil_boss") is not None:
        v0 = shell.volume
        want = PI * (v("coil_boss_d") / 2) ** 2 * v("coil_boss_h")
        delete_extrude(ctx, "coil_boss")
        shell = body_named(ctx, "shell")
        removed = v0 - shell.volume
        if abs(removed - want) > 0.02 * want:
            raise RuntimeError("coil boss removal took %.3f cm3, wanted %.3f" % (removed, want))
        print("coil boss removed: -%.3f cm3 (want %.3f)" % (removed, want))
    if abs(shell.boundingBox.minPoint.z) > 0.001:
        raise RuntimeError("shell underside is at z=%.3f mm, wanted 0" % (shell.boundingBox.minPoint.z * 10))
    adsk.doEvents()

    # ---- ring: delete round, extrude, sketch; rebuild without the hole ----------
    old_round = ctx.root.features.filletFeatures.itemByName("ring_round")
    ring_had_hole = ctx.root.sketches.itemByName("tpu_ring") is not None and \
        ctx.root.sketches.itemByName("tpu_ring").sketchCurves.sketchCircles.count == 3
    if ring_had_hole:
        if old_round is not None:
            old_round.deleteMe()
            adsk.doEvents()
        delete_extrude(ctx, "tpu_ring")
        if body_exists(ctx, "tpu_ring"):
            raise RuntimeError("tpu_ring body survived its extrude's deletion")
    if not body_exists(ctx, "tpu_ring"):
        pl = ctx.planes.itemByName("ring_plane")
        if pl is None:
            raise RuntimeError("ring_plane missing")
        sk = ctx.root.sketches.add(pl)
        sk.name = "tpu_ring"
        outer = centred_circle(ctx, sk, v("ring_od") / 2, "ring_od", 1)
        concentric_circle(ctx, sk, outer, v("ring_id") / 2, "ring_id", 2)
        if not sk.isFullyConstrained:
            raise RuntimeError("tpu_ring sketch not fully constrained")
        profs, n = loop_profiles(sk, 2)
        if n != 1:
            raise RuntimeError("tpu_ring expected one 2-loop profile, got %d" % n)
        want = PI * ((v("ring_od") / 2) ** 2 - (v("ring_id") / 2) ** 2) * v("ring_t")
        f, ring = ctx.checked_newbody(
            profs, "ring_t",
            lambda b: abs(b.boundingBox.maxPoint.z) < 0.01 and abs(b.boundingBox.minPoint.z + v("ring_t")) < 0.01
            and abs(b.volume - want) < 0.01 * want,
            "ring")
        f.name = "tpu_ring"
        ring.name = "tpu_ring"
        print("tpu ring rebuilt: %.2f cm3 (want %.2f), %d faces" % (ring.volume, want, ring.faces.count))
    adsk.doEvents()

    if ctx.root.features.filletFeatures.itemByName("ring_round") is None:
        Ro, Ri, z = v("ring_od") / 2, v("ring_id") / 2, -v("ring_t")
        edges = circle_edges(body_named(ctx, "tpu_ring"), [(0, 0, Ro, z), (0, 0, Ri, z)])
        r = v("ring_r")
        rounded(ctx, "ring_round", "tpu_ring", edges, "ring_r",
                corner_volume(Ro, r, True) + corner_volume(Ri, r, False))
    adsk.doEvents()

    # ---- dead parameters ------------------------------------------------------
    for name in DEAD_PARAMS:
        p = ctx.up.itemByName(name)
        if p is None:
            continue
        if not p.deleteMe():
            raise RuntimeError("parameter %s is still referenced; could not delete" % name)
        adsk.doEvents()
        print("deleted parameter", name)

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
