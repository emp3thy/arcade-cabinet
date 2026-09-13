"""Lap pad, D-014: the nested disc. Stage D -- edge fillets, in the document
that holds stages A, B and C. Fillets go last and minimal (face count
changes break index picks; every edge here is found by a geometric predicate,
R4). Four parametric constant-radius fillets, each bound to its own root:

  tyre_round   tyre_r on the TPU tyre's two outer edges (the r = tyre_od / 2
               circles at tyre_z0 and ridge_hi_z): the rounded equator that
               meets belly, thigh and knee (D-014).
  ring_round   ring_r on the TPU ring's two bottom edges (outer r = ring_od
               / 2 and inner r = ring_id / 2, both at z = -ring_t).
  plate_round  plate_r on the plate's top outer edge (r = plate_dia / 2 at
               plate_top_z), the edge a finger meets at the rebate.
  disc_round   disc_r on the seven raised discs' top outer edges (stick_disc_d
               / 2 round the stick, btn_disc_d / 2 round each button, at
               plate_top_z + disc_h).

Each fillet's removed volume is asserted against Pappus: a constant-radius
round on a circular edge of radius R removes a ring whose section is the
square-minus-quarter-disc corner, area r^2 (1 - pi/4), centroid 0.2234 r from
the corner, so V = 2 pi (R -/+ 0.2234 r) r^2 (1 - pi/4) (minus for an
outer edge, plus for an inner one). `filletFeatures.add()` can return success
while the fillet errors in the timeline (measured): healthState is read back.

Not modelled (still): port-board M3 holes (ASSUMED 24 x 20, wait for the
measurement), rim-band lettering, raised-disc colour split.
"""
FH_ATTEMPT = 1
FH_OPTS = {
    "only_params": ["tyre_r", "ring_r", "plate_r", "disc_r"],
    "liveness_budget_s": 120,
}
INTERFERENCE_ALLOWED = []
CLEARANCES = []
EXPECT_DEAD = []  # namespace is reused across executes; stage C set this
from fusionhelper.buildkit import *

import adsk.core
import adsk.fusion

PI = 3.141592653589793
CORNER_AREA = 1.0 - PI / 4.0      # of r^2
CORNER_CENTROID = 0.2234          # of r, from the corner

PARAMS_D = (
    ("tyre_r",  "10 mm",  "mm", "TPU tyre outer edge round; tyre wall is 12"),
    ("ring_r",  "2.5 mm", "mm", "TPU ring bottom edge round; ring is 6 thick"),
    ("plate_r", "1 mm",   "mm", "plate top outer edge round"),
    ("disc_r",  "0.8 mm", "mm", "raised disc top edge round; discs are 2 tall"),
)

NEEDED = ("tyre_od", "tyre_z0", "ridge_hi_z", "ring_od", "ring_id", "ring_t",
          "plate_dia", "plate_top_z", "disc_h", "stick_disc_d", "btn_disc_d",
          "stick_x", "stick_y")
BUTTONS = ("lp", "mp", "hp", "lk", "mk", "hk")


def ensure_params(ctx):
    for name in NEEDED:
        if ctx.up.itemByName(name) is None:
            raise RuntimeError("parameter %s missing: run stages A, B and C first" % name)
    for name, expr, unit, comment in PARAMS_D:
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


def fillet_exists(ctx, name):
    return ctx.root.features.filletFeatures.itemByName(name) is not None


def circle_edges(body, wants, tol=0.005):
    """Edges of body whose geometry is a full circle matching one of
    wants = [(cx, cy, r, z), ...] in cm. Every want must match exactly one
    edge (R4: predicate, not index)."""
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
        raise RuntimeError("edge match counts %s for wants %s; circles on %s: %s"
                           % (hits, [(round(a * 10, 1), round(b * 10, 1), round(r * 10, 2), round(z * 10, 2)) for a, b, r, z in wants],
                              body.name, sorted(set(seen))))
    return coll


def corner_volume(R, r, outer):
    """Pappus volume of a constant-radius round on a circular edge of radius
    R (cm); outer=True for an edge on the outside of the body (the centroid
    sits inside R), False for the edge of a hole."""
    rc = R - CORNER_CENTROID * r if outer else R + CORNER_CENTROID * r
    return 2.0 * PI * rc * r * r * CORNER_AREA


def rounded(ctx, name, body_name, edges, radius_param, want_cm3, tol=0.03):
    body = body_named(ctx, body_name)
    before = body.volume
    faces0 = body.faces.count
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
    print("%s: -%.4f cm3 (want %.4f), faces %d -> %d" % (name, removed, want_cm3, faces0, body.faces.count))
    return f


def run(_context: str):
    ctx = BuildCtx(adsk.core.Application.get())
    ensure_params(ctx)
    v = ctx.val

    # ---- tyre: two outer edges ----------------------------------------------
    if not fillet_exists(ctx, "tyre_round"):
        R = v("tyre_od") / 2
        edges = circle_edges(body_named(ctx, "tpu_tyre"),
                             [(0, 0, R, v("tyre_z0")), (0, 0, R, v("ridge_hi_z"))])
        r = v("tyre_r")
        rounded(ctx, "tyre_round", "tpu_tyre", edges, "tyre_r", 2 * corner_volume(R, r, True))
    adsk.doEvents()

    # ---- ring: bottom outer and bottom inner edges -----------------------------
    if not fillet_exists(ctx, "ring_round"):
        Ro, Ri, z = v("ring_od") / 2, v("ring_id") / 2, -v("ring_t")
        edges = circle_edges(body_named(ctx, "tpu_ring"), [(0, 0, Ro, z), (0, 0, Ri, z)])
        r = v("ring_r")
        rounded(ctx, "ring_round", "tpu_ring", edges, "ring_r",
                corner_volume(Ro, r, True) + corner_volume(Ri, r, False))
    adsk.doEvents()

    # ---- plate: top outer edge --------------------------------------------------
    if not fillet_exists(ctx, "plate_round"):
        R = v("plate_dia") / 2
        edges = circle_edges(body_named(ctx, "plate"), [(0, 0, R, v("plate_top_z"))])
        rounded(ctx, "plate_round", "plate", edges, "plate_r", corner_volume(R, v("plate_r"), True))
    adsk.doEvents()

    # ---- raised discs: seven top outer edges ------------------------------------
    if not fillet_exists(ctx, "disc_round"):
        z = v("plate_top_z") + v("disc_h")
        Rs, Rb = v("stick_disc_d") / 2, v("btn_disc_d") / 2
        wants = [(v("stick_x"), v("stick_y"), Rs, z)]
        for name in BUTTONS:
            wants.append((v(name + "_x"), v(name + "_y"), Rb, z))
        edges = circle_edges(body_named(ctx, "plate"), wants)
        r = v("disc_r")
        rounded(ctx, "disc_round", "plate", edges, "disc_r",
                corner_volume(Rs, r, True) + 6 * corner_volume(Rb, r, True))
    adsk.doEvents()

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
