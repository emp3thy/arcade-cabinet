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
from fusionhelper.buildkit import *

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
