"""Full-3D Blender build of 'The Doctor Who Tested His Own Heart'.
Usage:  python3 scenes.py <scene 1-7> render            -> renders/b3d/s<N>/####.png
        python3 scenes.py <scene 1-7> still <t_abs> out.png"""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from core import *
from scene_planner import SCENES
from timing import remap
import bpy, bmesh
from mathutils import Vector

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
T0 = 0.


def F(t):
    return int(round((t - T0) * FPS)) + 1


def nframes(i):
    return int(round((SCENES[i - 1]["t1"] - SCENES[i - 1]["t0"]) * FPS))


# ------------------------------------------------------------------ materials
def wood_mat(name="wood", col=(.32, .17, .08), scale=3., rough=.35):
    m = mat(name, col, rough, coat=.3); nt = m.node_tree; b = bsdf(m)
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale * .25, scale * 6, scale)
    wv = nt.nodes.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 3; wv.inputs["Distortion"].default_value = 6; wv.inputs["Detail"].default_value = 3
    rp = nt.nodes.new("ShaderNodeValToRGB"); rp.color_ramp.elements[0].color = (*[c * .78 for c in col], 1); rp.color_ramp.elements[1].color = (*[min(1, c * 1.1) for c in col], 1)
    nt.links.new(tc.outputs["Object"], mp.inputs[0]); nt.links.new(mp.outputs[0], wv.inputs[0]); nt.links.new(wv.outputs["Fac"], rp.inputs[0]); nt.links.new(rp.outputs[0], b.inputs["Base Color"])
    return m


def checker_mat(name, c1, c2, scale=8., rough=.25, coat=.4):
    m = mat(name, c1, rough, coat=coat); nt = m.node_tree; b = bsdf(m)
    ck = nt.nodes.new("ShaderNodeTexChecker"); ck.inputs["Scale"].default_value = scale
    ck.inputs["Color1"].default_value = (*c1, 1); ck.inputs["Color2"].default_value = (*c2, 1)
    tc = nt.nodes.new("ShaderNodeTexCoord"); nt.links.new(tc.outputs["Object"], ck.inputs[0]); nt.links.new(ck.outputs["Color"], b.inputs["Base Color"])
    return m


def tile_mat(name, col, grout=(.6, .62, .6), scale=6., rough=.15):
    m = mat(name, col, rough, coat=.6); nt = m.node_tree; b = bsdf(m)
    br = nt.nodes.new("ShaderNodeTexBrick"); br.inputs["Scale"].default_value = scale; br.inputs["Mortar Size"].default_value = .015
    br.offset = 0.; br.inputs["Color1"].default_value = (*col, 1); br.inputs["Color2"].default_value = (*[c * .93 for c in col], 1); br.inputs["Mortar"].default_value = (*grout, 1)
    br.inputs["Brick Width"].default_value = .5; br.inputs["Row Height"].default_value = .5
    tc = nt.nodes.new("ShaderNodeTexCoord"); nt.links.new(tc.outputs["Object"], br.inputs[0]); nt.links.new(br.outputs["Color"], b.inputs["Base Color"])
    return m


def deform_sphere(name, loc, fn, m, u=48, v=32, sub=1):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=1.)
    for vt in bm.verts: vt.co = Vector(fn(*vt.co))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me); link(o); o.location = loc; me.materials.append(m)
    if sub: md = o.modifiers.new("sub", 'SUBSURF'); md.levels = sub; md.render_levels = sub
    return o


def heart_model(loc, s=1., m=None, vessels=True):
    """Stylised anatomical heart: ventricles + atria + aorta arch + vena cava + pulmonary trunk."""
    m = m or mat("heart", (.55, .05, .06), .28, sss=.35, sss_rad=(1., .2, .1), coat=.7, bump=.35, bump_scale=40)
    root = empty("heart_root", loc)

    def vent(x, y, z):
        k = (1 - z) * .5                      # 0 top .. 1 apex
        r = 1 - .55 * k ** 1.6
        return (x * .5 * r * s, y * .42 * r * s, z * .62 * s)
    h = deform_sphere("ventricles", loc, vent, m); h.rotation_euler = (0, math.radians(-25), math.radians(15)); h.parent = root; h.location = (0, 0, 0)
    for dx, dz, sc in ((-.2, .42, .26), (.18, .4, .24)):
        a = prim("uv_sphere", (dx * s, .02 * s, dz * s), (sc * s, sc * .9 * s, sc * .85 * s), m, sub=1); a.parent = root
    if vessels:
        vm = mat("aorta", (.72, .12, .12), .3, sss=.3, coat=.6)
        bv = mat("vcava", (.2, .22, .6), .3, sss=.3, coat=.6)
        for pts, r, mm in ((((.02, 0, .45), (.05, 0, .85), (.3, .05, 1.0), (.5, .1, .8), (.5, .15, .3)), .1, vm),
                           (((-.25, .05, .5), (-.28, .05, 1.1)), .08, bv),
                           (((.1, -.1, .5), (.0, -.15, .8), (-.3, -.1, .95)), .08, mat("pulm", (.35, .3, .65), .3, coat=.5))):
            t = curve_tube([Vector(p) * s for p in pts], r * s, mm, "vessel"); t.parent = root
    # coronary vessels on the surface
    cm = mat("coronary", (.75, .55, .15), .35, coat=.5)
    for k in range(5):
        a0 = k * 1.2
        pts = [(.42 * math.cos(a0 + z * .5) * (1 - .4 * z) * s, -.35 * math.sin(a0 + z * .5) * (1 - .4 * z) * s, (.3 - z * .75) * s) for z in (0, .3, .6, .9)]
        t = curve_tube(pts, .012 * s, cm, "cor"); t.parent = h
    return root, h


def beat(o, base, f_beats, amp=.07):
    for fb in f_beats:
        key(o, fb, scale=base); key(o, fb + 3, scale=tuple(b * (1 + amp) for b in base)); key(o, fb + 7, scale=tuple(b * (1 - amp * .3) for b in base)); key(o, fb + 12, scale=base)


def heart_beats(t0, t1):
    """Absolute times of heartbeats (shared with the SFX thumps)."""
    out = []; k = 0
    while True:
        tb = remap(k * .86); k += 1
        if tb > t1: break
        if tb >= t0: out.append(tb)
    return out


# ------------------------------------------------------------------ sets
def office(red=0.):
    floor = rbox((0, 0, -.05), (9, 9, .1), wood_mat("floor", (.3, .16, .07), 2.), bevel=0)
    wall_m = mat("wall", (.42 + red * .2, .45 - red * .15, .33 - red * .1), .8, bump=.1, bump_scale=60)
    pan_m = wood_mat("panel", (.22, .1, .045), 1.5)
    rbox((0, 1.8, 1.6), (9, .1, 3.2), wall_m, bevel=0); rbox((-2.6, 0, 1.6), (.1, 9, 3.2), wall_m, bevel=0)
    rbox((0, 1.72, .5), (9, .08, 1.0), pan_m, .01); rbox((-2.52, 0, .5), (.08, 9, 1.0), pan_m, .01)
    rbox((0, 1.68, 1.02), (9, .06, .05), pan_m, .01)
    # window (back wall) with bright sky + sun
    win = rbox((1.6, 1.74, 1.75), (1.3, .02, 1.5), mat("sky", (1, .95, .85), emit=4.), bevel=0)
    fm = wood_mat("frame", (.85, .82, .75), 1)
    for x in (1.0, 1.6, 2.2): rbox((x, 1.7, 1.75), (.06, .08, 1.55), fm, .01)
    for z in (1.0, 1.75, 2.5): rbox((1.6, 1.7, z), (1.3, .08, .06), fm, .01)
    light('SUN', (1.6, 4, 3), 4. + red, (1, .82, .6), .05, target=(.2, -.8, 0), name="sun")
    # desk + lamp + books + papers
    dm = wood_mat("desk", (.25, .11, .05), 2.5, .25)
    rbox((-1.45, .85, .76), (1.5, .8, .06), dm, .01)
    for x in (-2.1, -.8):
        for y in (.55, 1.15): rbox((x, y, .38), (.06, .06, .76), dm, .01)
    rbox((-1.45, .85, .55), (1.4, .7, .3), dm, .01)
    lamp_m = mat("brass", (.85, .6, .25), .2, metal=1)
    prim("cylinder", (-2.0, 1.0, .8), (.08, .08, .015), lamp_m, vertices=32)
    prim("cylinder", (-2.0, 1.0, 1.0), (.008, .008, .2), lamp_m, vertices=12)
    prim("cone", (-2.0, .95, 1.2), (.12, .12, .09), mat("shade", (.05, .3, .12), .3, coat=.8), rot=(math.radians(-25), 0, 0), vertices=32)
    light('POINT', (-2.0, .9, 1.13), 25, (1, .75, .45), .03, name="lamp")
    bk = [(.5, .08, .06), (.08, .2, .35), (.12, .3, .1), (.45, .35, .1)]
    for i, c in enumerate(bk): rbox((-1.0 + i * .045, 1.1, .88), (.04, .2, .18 + .02 * (i % 2)), mat(f"book{i}", c, .5), .004)
    for i in range(3): rbox((-1.6 + i * .05, .75, .795 + i * .004), (.21, .29, .003), mat("paper", (.92, .9, .82), .7), 0, rot=(0, 0, .2 * i))
    # bookshelf on left wall
    for z in (.3, .75, 1.2, 1.65, 2.1):
        rbox((-2.35, -.6, z), (.35, 1.4, .04), dm, .005)
        rnd = random.Random(int(z * 10))
        y = -1.25
        while y < .05:
            w = rnd.uniform(.03, .06); hgt = rnd.uniform(.25, .38)
            rbox((-2.35, y, z + .02 + hgt / 2), (.24, w, hgt), mat("b", rnd.choice(bk), .55), .004); y += w + .004
    # wall calendar 1929
    rbox((-.6, 1.73, 1.95), (.5, .02, .62), mat("cal", (.93, .9, .82), .6), .004)
    rbox((-.6, 1.72, 2.2), (.5, .02, .12), mat("calred", (.6, .05, .04), .5), .004)
    text("1929", (-.6, 1.71, 1.88), .2, mat("caltxt", (.08, .06, .05), .5), extrude=.002)
    # anatomy poster
    rbox((.45, 1.73, 1.95), (.55, .02, .75), mat("poster", (.88, .84, .72), .7), .004)
    hr, _ = heart_model((.45, 1.70, 1.95), .22, vessels=False)
    for o in [hr] + list(hr.children): o.scale = (1, .25, 1) if o == hr else o.scale
    # ceiling bounce
    light('AREA', (0, -1.5, 3.2), 150, (1, .92, .8), 4, target=(0, 0, 0), name="bounce")
    world_color((.25, .2, .17), .6)


def tube_coil(loc, m):
    o = prim("torus", loc, (.045, .045, .045), m, rot=(math.pi / 2, 0, 0), major_radius=1, minor_radius=.06, sub=0, major_segments=48)
    o2 = prim("torus", (loc[0], loc[1], loc[2] - .01), (.04, .04, .04), m, rot=(math.pi / 2, .3, 0), major_radius=1, minor_radius=.065, sub=0, major_segments=48)
    return o, o2


# ------------------------------------------------------------------ scene 1: forbidden (office)
def scene1():
    office()
    boss_ = boss("Boss", (-.5, 0, 0), math.pi / 2)
    doc = doctor("Doc", (.52, 0, 0), -math.pi / 2)
    rub = mat("rubber", (.75, .45, .15), .35, coat=.6, sss=.2)
    c1, c2 = tube_coil(Vector(JOINTS["hd.R"]) + Vector((0, -.03, -.03)), rub)
    for o in (c1, c2): doc.attach(o, "hand.R", rest_space=True)
    n = nframes(1)
    # idle / breathing
    for f in range(1, n + 1, 20):
        doc.pose(f, chest=(2 + 1.5 * math.sin(f * .2), 0, 0)); boss_.pose(f, chest=(4 + 1.5 * math.sin(f * .17), 0, 0))
    # doc eagerly holds up the catheter coil
    doc.pose(1, uarm_R=(-15, 0, 5), farm_R=(-30, 0, 0), uarm_L=(0, 0, -4), farm_L=(-10, 0, 0), head=(0, 0, 0))
    doc.pose(F(1.9), uarm_R=(-15, 0, 5), farm_R=(-30, 0, 0))
    doc.pose(F(2.4), uarm_R=(-55, 0, 12), farm_R=(-60, 0, 0), head=(-4, 0, 0))
    doc.pose(n, uarm_R=(-58, 0, 12), farm_R=(-62, 0, 0), head=(-6, 0, 0))
    doc.brows(1, .3); doc.brows(F(2.4), .8); doc.mouth(1, 0, 1.2); doc.mouth(F(2.4), .2, 1.3)
    doc.brows(F(3.5), 1.); doc.mouth(F(3.6), .45, .9)
    # boss: arms crossed-ish, then thrusts a pointing finger "NEVER"
    boss_.pose(1, uarm_R=(-20, 0, -8), farm_R=(-95, 0, 0), uarm_L=(-20, 0, 8), farm_L=(-95, 0, 0), head=(5, 0, 0))
    boss_.pose(F(3.1), uarm_R=(-20, 0, -8), farm_R=(-95, 0, 0), head=(5, 0, 0), chest=(4, 0, 0))
    boss_.pose(F(3.4), uarm_R=(-82, 0, -14), farm_R=(-8, 0, 0), head=(-6, 0, 0), chest=(12, 0, 0))
    for k, f in enumerate(range(F(3.5), n, 5)):
        boss_.pose(f, farm_R=(-8 - 8 * (k % 2), 0, 0))
    boss_.brows(1, -.4); boss_.brows(F(3.2), -1.)
    boss_.talk(F(3.36), F(4.45), 1.); boss_.mouth(1, 0)
    boss_.blink([20, 95]); doc.blink([35, 110])
    cam = Cam(fstop=1.8)
    cam.shot(1, F(1.6), (-.6, 1.05, 1.92), (-.15, -1.6, 1.7), (-.6, 1.72, 1.92), (0, 0, 1.5), 50, 30)
    cam.shot(F(1.6) + 1, F(3.2), (-1.25, -.55, 1.72), (-1.05, -.42, 1.7), (.52, 0, 1.66), (.52, 0, 1.68), 55, 60, fstop=1.6)
    cam.shot(F(3.2) + 1, n, (.32, -.55, 1.42), (.18, -.42, 1.46), (-.5, 0, 1.6), (-.5, 0, 1.64), 30, 34, fstop=2.2)
    cam.handheld(.01)


# ------------------------------------------------------------------ arm prop (scene 2 macro + cutaway)
def arm_prop(O, skin):
    """Forearm+hand lying along +X (hand at O). Returns (opaque arm, ghost arm, vein curve points)."""
    O = Vector(O)
    pts = [(0, 0, 0), (.07, 0, .005), (.16, 0, .015), (.3, 0, .025), (.42, 0, .035), (.52, 0, .045), (.7, 0, .06)]
    rad = [(.035, .015), (.042, .02), (.03, .022), (.036, .03), (.042, .036), (.047, .042), (.055, .05)]
    verts = [O + Vector(p) for p in pts]; edges = [(i, i + 1) for i in range(len(pts) - 1)]
    # fingers
    for k, oy in enumerate((-.024, -.008, .008, .024)):
        b0 = len(verts); ln = (.055, .065, .06, .048)[k]
        for j, t in enumerate((0, .5, 1.)):
            verts.append(O + Vector((-.02 - ln * t, oy, -.005 - .01 * t))); rad.append((.0095 - .002 * t, .0085 - .002 * t))
        edges += [(0, b0), (b0, b0 + 1), (b0 + 1, b0 + 2)]
    b0 = len(verts)
    for j, t in enumerate((0, .5, 1.)):
        verts.append(O + Vector((.03 - .045 * t, -.035 - .015 * t, .0 + .005 * t))); rad.append((.012 - .002 * t, .011 - .002 * t))
    edges += [(1, b0), (b0, b0 + 1), (b0 + 1, b0 + 2)]
    me = bpy.data.meshes.new("armprop"); me.from_pydata([tuple(v) for v in verts], edges, [])
    o = bpy.data.objects.new("armprop", me); link(o)
    sk = o.modifiers.new("skin", 'SKIN'); sk.use_smooth_shade = True
    for i, r in enumerate(rad): me.skin_vertices[0].data[i].radius = r
    me.skin_vertices[0].data[3].use_root = True
    ss = o.modifiers.new("sub", 'SUBSURF'); ss.levels = 2; ss.render_levels = 3
    me.materials.append(skin)
    ghost = o.copy(); ghost.data = me.copy(); link(ghost); ghost.data.materials.clear(); ghost.data.materials.append(ghost_mat("armghost", (1., .7, .55), .1, .2))
    vein = [O + Vector(p) for p in ((.06, -.012, .028), (.18, -.006, .042), (.3, .004, .05), (.42, .0, .062), (.55, -.004, .075), (.72, -.002, .09))]
    return o, ghost, vein


def scene2():
    n = nframes(2)
    # --- operating room set (shot A) ---
    tile = tile_mat("otile", (.55, .72, .68), scale=7)
    rbox((0, 2.2, 1.6), (8, .1, 3.2), tile, 0); rbox((-2.4, 0, 1.6), (.1, 8, 3.2), tile, 0)
    rbox((0, 0, -.05), (8, 8, .1), checker_mat("ofloor", (.55, .58, .55), (.35, .4, .38), 18), 0)
    steel = mat("steel", (.75, .75, .78), .25, metal=1)
    rbox((0, .55, .85), (1.9, .7, .08), steel, .01)                                     # operating table
    rbox((0, .55, .89), (1.85, .66, .02), mat("sheet", (.2, .45, .4), .7, sheen=.5), .01)
    for x in (-.8, .8): prim("cylinder", (x, .55, .42), (.03, .03, .42), steel, vertices=16)
    prim("cylinder", (.2, -.05, .25), (.2, .2, .025), steel, vertices=32)                # stool
    prim("cylinder", (.2, -.05, .12), (.025, .025, .12), steel, vertices=12)
    # tray with syringe + catheter coil
    rbox((-.5, .45, .91), (.4, .25, .02), steel, .005)
    rub = mat("rubber", (.75, .45, .15), .35, coat=.6, sss=.2)
    prim("torus", (-.45, .45, .93), (.06, .06, .06), rub, major_radius=1, minor_radius=.06, sub=0)
    # overhead surgical lamp
    lm = mat("lampbody", (.8, .82, .8), .3, coat=.5)
    prim("cylinder", (0, .4, 2.35), (.38, .38, .08), lm, vertices=48)
    prim("cylinder", (0, .4, 2.29), (.32, .32, .01), mat("lampglow", (1, .97, .9), emit=12), vertices=48)
    light('SPOT', (0, .4, 2.25), 900, (1, .96, .9), .3, target=(0, .4, .9), spot=math.radians(70), name="oplamp")
    light('AREA', (-1.5, -2.5, 1.8), 60, (.5, .7, 1.), 3, target=(0, .3, 1.), name="moon")
    # door with light leak (he glances back at it)
    rbox((1.7, 2.14, 1.05), (.95, .06, 2.1), mat("door", (.6, .66, .62), .5, coat=.3), .01)
    rbox((1.2, 2.12, 1.05), (.03, .02, 2.0), mat("leak", (1, .8, .5), emit=8), 0)
    world_color((.03, .05, .07), .5)
    doc = doctor("Doc", (.2, -.05, -.43), 0)
    for f in (1, n):
        doc.pose(f, thigh_L=(-88, 0, 0), thigh_R=(-88, 0, 0), shin_L=(88, 0, 0), shin_R=(88, 0, 0), foot_L=(0, 0, 0), foot_R=(0, 0, 0))
    doc.move(1, yaw=math.pi); doc.move(n, yaw=math.pi)
    # facing the table (+Y); left arm resting on table, right arm reaching to tray; glance back to door at ~5.7s
    doc.pose(1, uarm_L=(-62, 0, -8), farm_L=(-25, 0, 0), uarm_R=(-55, 0, 10), farm_R=(-40, 0, 0), head=(12, 0, 0), chest=(14, 0, 0))
    doc.pose(F(5.4), head=(12, 0, 0)); doc.pose(F(5.75), head=(0, 70, 8)); doc.pose(F(6.35), head=(0, 72, 8)); doc.pose(F(6.7), head=(14, 0, 0))
    doc.brows(1, .2); doc.brows(F(5.75), .9); doc.brows(F(6.6), -.3); doc.blink([10, F(6.4)])
    doc.lids(1, -28)
    cam = Cam(fstop=2.)
    cam.shot(1, F(6.7), (1.5, -1.0, 1.55), (1.25, -.75, 1.45), (.2, .1, 1.2), (.25, .2, 1.25), 32, 38)
    # --- macro arm on surgical cloth (shots B, C) located away from the room ---
    O = Vector((30, 0, 1.0))
    rbox(O + Vector((.3, 0, -.06)), (1.6, 1.0, .02), mat("cloth", (.12, .38, .33), .85, sheen=.6, bump=.4, bump_scale=300), .005)
    three_point(O + Vector((.25, 0, 0)), 30, 8, 30, scale=.5)
    light('SPOT', O + Vector((.2, -.1, 1.2)), 300, (1, .96, .9), .2, target=O + Vector((.25, 0, 0)), spot=math.radians(50))
    skin = skin_mat("armskin", (.72, .42, .29))
    arm, ghost, vp = arm_prop(O, skin)
    vein_m = mat("veinm", (.12, .2, .7), .2, coat=.6, emit=.5, emit_col=(.1, .2, .9), alpha=.35)
    vein = curve_tube(vp, .0065, vein_m, "vein")
    art = curve_tube([p + Vector((0, .018, -.008)) for p in vp], .005, mat("artm", (.75, .05, .05), .3, coat=.6, emit=.5, emit_col=(.8, .05, .05)), "artery")
    cath = curve_tube([vp[0] + Vector((-.12, -.03, .06)), vp[0] + Vector((-.02, -.01, .01))] + vp[1:], .0042, mat("cath", (1., .6, .2), .25, coat=.8, emit=5., emit_col=(1, .55, .1)), "cath")
    fB, fC = F(6.7) + 1, F(8.2) + 1
    for o in (vein, art, ghost):
        o.hide_render = True; o.keyframe_insert("hide_render", frame=1); o.hide_render = False; o.keyframe_insert("hide_render", frame=fC)
    arm.hide_render = False; arm.keyframe_insert("hide_render", frame=1); arm.hide_render = True; arm.keyframe_insert("hide_render", frame=fC)
    cath.hide_render = True; cath.keyframe_insert("hide_render", frame=1); cath.hide_render = False; cath.keyframe_insert("hide_render", frame=fC)
    set_interp(arm); set_interp(ghost); set_interp(vein); set_interp(art); set_interp(cath)
    grow(cath, fC, F(10.1), .02, 1.)
    # syringe: glass barrel, steel needle, plunger
    syr = empty("syringe"); glass = mat("glass", (.9, .97, 1.), .03, trans=1., coat=1.)
    for p, s_, m_ in (((0, 0, .07), (.011, .011, .055), glass), ((0, 0, .008), (.006, .006, .008), mat("hub", (.1, .6, .5), .3)),
                      ((0, 0, -.03), (.0011, .0011, .03), steel)):
        o = prim("cylinder", p, s_, m_, vertices=24); o.parent = syr
    liq = prim("cylinder", (0, 0, .06), (.009, .009, .04), mat("liq", (.85, .95, 1.), .05, trans=.9, emit=.2), vertices=24); liq.parent = syr
    pl = prim("cylinder", (0, 0, .16), (.0045, .0045, .06), mat("plunger", (.9, .9, .9), .4), vertices=16); pl.parent = syr
    tip = O + Vector((.12, -.005, .04))
    syr.scale = (.6, .6, .6)
    syr.rotation_euler = (math.radians(-35), math.radians(-30), 0)
    key(syr, fB, location=tip + Vector((.08, -.12, .16))); key(syr, F(7.25), location=tip + Vector((.035, -.045, .055)))
    key(syr, F(7.8), location=tip + Vector((.035, -.045, .055))); key(syr, F(8.2), location=tip + Vector((.1, -.15, .2)))
    key(liq, F(7.25), scale=(.009, .009, .04)); key(liq, F(7.8), scale=(.009, .009, .008))
    key(pl, F(7.25), location=(0, 0, .16)); key(pl, F(7.8), location=(0, 0, .105))
    # skin numbing ripple: subtle emissive bloom at injection site
    glow = prim("uv_sphere", tip + Vector((0, 0, -.012)), (.001, .001, .001), mat("numb", (.6, .8, 1.), emit=2.), sub=1)
    key(glow, F(7.3), scale=(.001, .001, .001)); key(glow, F(7.9), scale=(.03, .03, .004)); key(glow, F(8.2), scale=(.04, .04, .002)); key(glow, fC, scale=(0, 0, 0))
    cam.shot(fB, F(8.2), O + Vector((.32, -.42, .26)), O + Vector((.26, -.33, .2)), tip + Vector((.02, 0, .0)), tip + Vector((0, 0, .0)), 38, 45, fstop=5.6)
    cam.shot(fC, n, O + Vector((.0, -.3, .22)), O + Vector((.45, -.3, .24)), vp[0] + Vector((.05, 0, 0)), vp[-2] + Vector((0, 0, 0)), 35, 35, fstop=6.)
    cam.handheld(.003)


# ------------------------------------------------------------------ scene 3: inside the vein -> ghost body + heart
def scene3():
    n = nframes(3)
    fB = F(12.9) + 1
    # --- vein tunnel ---
    V = Vector((0, 0, 0))
    path = [V + Vector((i * 2.0, math.sin(i * .9) * .35, math.cos(i * .6) * .25)) for i in range(12)]
    wall = mat("veinwall", (.45, .03, .05), .35, sss=.6, sss_rad=(1, .2, .1), coat=.5, bump=1.2, bump_scale=6)
    tun = curve_tube(path, 1.0, wall, "tunnel", res=12)
    cell_m = mat("rbc", (.7, .03, .05), .3, sss=.5, sss_rad=(1, .2, .1), coat=.6)
    rnd = random.Random(3)
    from mathutils import geometry
    pt = lambda u: path[0].lerp(path[-1], u)
    for i in range(70):
        u = rnd.uniform(0, 1); base = Vector((u * 22, 0, 0))
        idx = min(10, int(base.x / 2)); c = path[idx].lerp(path[idx + 1], (base.x - idx * 2) / 2)
        off = Vector((0, rnd.uniform(-.6, .6), rnd.uniform(-.6, .6)))
        if off.length > .7: off *= .7 / off.length
        o = prim("torus", c + off, (.13, .13, .13), cell_m, rot=(rnd.random() * 3, rnd.random() * 3, 0), major_radius=1, minor_radius=.55, sub=1, major_segments=24, minor_segments=12)
        o.scale = (.13, .13, .09)
        key(o, 1, location=c + off, rotation_euler=o.rotation_euler); key(o, fB - 1, location=c + off + Vector((-3.5, rnd.uniform(-.1, .1), rnd.uniform(-.1, .1))),
                                                                          rotation_euler=Euler((o.rotation_euler.x + 2, o.rotation_euler.y + 1, 0)))
    for fc in all_fcurves(o): pass
    cath_m = mat("cath", (1., .6, .2), .25, coat=.8, emit=2., emit_col=(1, .5, .1))
    cpath = [p + Vector((0, 0, -.35)) for p in path]
    cath = curve_tube(cpath, .07, cath_m, "cath3"); grow(cath, 1, fB - 1, .1, .62)
    tipl = light('POINT', path[1], 120, (1, .6, .3), .2, name="tiplight")
    # camera rides behind the catheter tip
    seg = lambda u: (lambda i: path[i].lerp(path[i + 1], u * 11 - i))(min(10, int(u * 11)))
    for f in range(1, fB, 6):
        u = .1 + (.62 - .1) * (f - 1) / (fB - 2)
        tipp = seg(u) + Vector((0, 0, -.35))
        key(tipl, f, location=tipp + Vector((0, 0, .3)))
    cam = Cam(fstop=2.8)
    cam.shot(1, fB - 1, seg(.03) + Vector((0, 0, .12)), seg(.5) + Vector((0, 0, .12)), seg(.1) + Vector((0, 0, -.2)), seg(.62) + Vector((0, 0, -.25)), 22, 22)
    light('POINT', path[0], 40, (1, .4, .3), .5)
    # --- ghost body with glowing heart (shot B) located elsewhere ---
    G = Vector((60, 0, 0))
    world_color((.0, .01, .03), 1.)
    d = doctor("Ghost", tuple(G), 0)
    gm = ghost_mat("ghostbody", (.4, .75, 1.), .05, .3)
    set_all_mats([o for o in bpy.data.objects if o.name.startswith("Ghost") or (o.parent == d.rig)], gm)
    for o in bpy.data.objects:
        if o.parent and o.parent.parent == d.rig: o.data.materials.clear() if o.type == 'MESH' else None; o.data.materials.append(gm) if o.type == 'MESH' else None
    d.pose(1, uarm_L=(-10, 0, -25), farm_L=(-10, 0, 0), uarm_R=(-5, 0, 15)); d.pose(n, uarm_L=(-10, 0, -25), farm_L=(-10, 0, 0))
    hp = G + Vector((.04, -.02, 1.3))
    hroot, hv = heart_model(hp, .085, mat("hglow", (.8, .05, .08), .3, sss=.3, coat=.6, emit=1.2, emit_col=(1, .05, .1)))
    beat(hroot, (1, 1, 1), [F(t) for t in heart_beats(12.9, 14.8)], .1)
    bpy.context.view_layer.update()
    W = lambda j: d.rig.matrix_world @ Vector(JOINTS[j])
    sh = W("sh.L"); el = W("el.L"); wr = W("wr.L")
    pts = [el + (wr - el) * .1, el + Vector((0, -.01, 0)), (el + sh) / 2, sh + Vector((-.02, 0, .0)), Vector(JOINTS["chest"]) + G + Vector((.1, -.02, .08)), hp + Vector((-.03, -.01, .05)), hp + Vector((-.02, -.01, .0))]
    gc = curve_tube(pts, .006, mat("gcath", (1, .6, .15), emit=8, emit_col=(1, .55, .1)), "gcath")
    grow(gc, fB, F(14.3), .05, 1.)
    light('POINT', hp + Vector((0, -.15, 0)), 6, (1, .2, .2), .1)
    cam.shot(fB, n, G + Vector((.9, -1.9, 1.35)), G + Vector((.25, -.62, 1.32)), G + Vector((.15, 0, 1.25)), hp, 35, 42, fstop=2.)


# ------------------------------------------------------------------ scene 4: corridor walk
def scene4():
    n = nframes(4); fB = F(16.8) + 1
    floor = rbox((0, 0, -.05), (40, 3.2, .1), checker_mat("cfloor", (.78, .74, .62), (.22, .35, .3), 1.6, .2, .6), 0)
    wl = mat("cwall", (.75, .72, .6), .7, bump=.05); wd = mat("cwainscot", (.25, .4, .35), .4, coat=.4)
    for y, sgn in ((1.6, 1), (-1.6, -1)):
        rbox((0, y, 1.7), (40, .1, 3.4), wl, 0); rbox((0, y - sgn * .06, .6), (40, .04, 1.2), wd, 0)
    rbox((0, 0, 3.4), (40, 3.2, .1), mat("ceil", (.85, .85, .8), .8), 0)
    for x in range(-18, 19, 3):
        prim("cylinder", (x, 0, 3.3), (.18, .18, .05), mat("clamp", (1, .95, .85), emit=10), vertices=24)
        light('POINT', (x, 0, 3.1), 60, (1, .9, .75), .3)
    for x in range(-17, 18, 3):   # doors on back wall
        rbox((x, 1.53, 1.05), (.9, .06, 2.1), wood_mat("cdoor", (.3, .15, .07), 1.5), .01)
        prim("uv_sphere", (x + .35, 1.48, 1.0), (.03, .03, .03), mat("knob", (.9, .7, .3), .2, metal=1))
    for x in range(-16, 19, 3):   # windows on near wall -> sun streaks on floor
        rbox((x, -1.56, 1.9), (1.0, .02, 1.3), mat("cwin", (1, .95, .85), emit=3), 0)
    light('SUN', (0, -5, 4), 3.5, (1, .85, .65), .03, target=(1, 1, 0), name="sun")
    # end door with X-RAY sign
    rbox((19.5, 0, 1.3), (.1, 1.4, 2.6), mat("xdoor", (.75, .78, .76), .4, coat=.4), .01)
    text("X-RAY", (19.42, 0, 2.85), .32, mat("xsign", (.4, .8, 1.), emit=8), rot=(math.pi / 2, 0, -math.pi / 2), extrude=.01)
    rbox((19.43, 0, 2.85), (.02, 1.1, .45), mat("signbg", (.02, .03, .05), .3), .01)
    world_color((.1, .1, .1), .4)
    doc = doctor("Doc")
    rub = mat("rubber", (.75, .45, .15), .35, coat=.6, sss=.2)
    # dangling catheter from the left inner elbow (bone-attached curve)
    el = Vector(JOINTS["el.L"]); wr = Vector(JOINTS["wr.L"])
    p0 = el + (wr - el) * .15 + Vector((-.03, -.035, 0))
    hang = curve_tube([p0, p0 + Vector((-.01, -.04, -.12)), p0 + Vector((.0, -.03, -.3)), p0 + Vector((.02, .0, -.42))], .004, rub, "hang")
    doc.attach(hang, "farm.L", rest_space=True)
    tape = prim("cube", tuple(p0 + Vector((.012, -.012, 0))), (.025, .004, .02), mat("tape", (.95, .93, .85), .7), smooth=False)
    tape.rotation_euler = (0, 0, math.radians(-30)); doc.attach(tape, "farm.L", rest_space=True)
    # walk 14.8 -> 18.7 along +X ; side tracking then follow-behind toward X-RAY door
    x0 = -1.5; speed = 1.35; x1 = x0 + speed * (n / FPS)
    doc.walk(1, n, (x0, 0, 0), (x1, 0, 0), cadence=2.1, arm=14)
    for f in range(1, n + 1, 2):
        doc.pose(f, uarm_L=(-8, 0, -6), farm_L=(-35, 0, 0))        # keeps the tubed arm bent and still
    doc.brows(1, .5); doc.blink([25, 80])
    cam = Cam(fstop=2.2)
    xb = x0 + speed * (fB - 1) / FPS
    cam.shot(1, fB - 1, (x0 - .2, -1.35, 1.25), (xb + .1, -1.35, 1.3), (x0 + .2, 0, 1.15), (xb + .3, 0, 1.2), 26, 30)
    cam.shot(fB, n, (xb - 1.6, -.25, 1.55), (x1 - .7, -.15, 1.6), (xb + 4, 0, 1.6), (19.4, 0, 2.2), 32, 45, fstop=4.)
    set_interp(cam.o, 'LINEAR'); set_interp(cam.t, 'LINEAR')
    cam.handheld(.012)


# ------------------------------------------------------------------ scene 5: X-ray
def xray_image(O, s=1., glow=1.):
    """Fluoroscope image: ribs, spine, clavicles, heart shadow, bright catheter."""
    bone = mat("xbone", (.6, .8, 1.), emit=2.2 * glow, emit_col=(.55, .8, 1.))
    objs = []
    for i in range(11):
        objs.append(prim("uv_sphere", O + Vector((0, 0, (.55 - i * .11) * s)), (.03 * s, .01, .04 * s), bone, sub=0))
    for k in range(8):
        y0 = (.42 - k * .1) * s; w = (.24 + .04 * min(k, 4)) * s
        for sg in (-1, 1):
            objs.append(curve_tube([O + Vector((sg * .03 * s, 0, y0)), O + Vector((sg * w * .7, 0, y0 + .04 * s)), O + Vector((sg * w, 0, y0 - .06 * s)),
                                    O + Vector((sg * w * .8, 0, y0 - .2 * s)), O + Vector((sg * .1 * s, 0, y0 - .28 * s))], .011 * s, bone, "rib"))
    for sg in (-1, 1):
        objs.append(curve_tube([O + Vector((sg * .04 * s, 0, .5 * s)), O + Vector((sg * .2 * s, 0, .55 * s)), O + Vector((sg * .4 * s, 0, .58 * s))], .016 * s, bone, "clav"))
        objs.append(prim("uv_sphere", O + Vector((sg * .45 * s, 0, .55 * s)), (.08 * s, .01, .07 * s), bone, sub=1))
    hm = mat("xheart", (.25, .45, .7), emit=1.0 * glow, emit_col=(.25, .45, .75))
    h = prim("uv_sphere", O + Vector((-.06 * s, .004, .02 * s)), (.17 * s, .004, .2 * s), hm, rot=(0, math.radians(-25), 0), sub=1)
    cath = curve_tube([O + Vector((.6 * s, -.005, .62 * s)), O + Vector((.42 * s, -.005, .58 * s)), O + Vector((.12 * s, -.005, .45 * s)), O + Vector((-.02 * s, -.005, .25 * s)), O + Vector((-.06 * s, -.005, .1 * s))],
                      .009 * s, mat("xcath", (1, 1, 1), emit=12 * glow), "xcath")
    return objs, h, cath


def scene5():
    n = nframes(5); fB = F(20.3) + 1; fC = F(21.15) + 1
    rbox((0, 0, -.05), (10, 10, .1), mat("xfloor", (.12, .13, .14), .3, coat=.4), 0)
    wall = tile_mat("xtile", (.2, .27, .3), scale=5)
    rbox((0, 2.5, 1.6), (10, .1, 3.2), wall, 0); rbox((-2.5, 0, 1.6), (.1, 10, 3.2), wall, 0)
    world_color((.01, .015, .025), .5)
    metal = mat("xmetal", (.25, .27, .3), .3, metal=.9); cream = mat("xcream", (.75, .72, .62), .45, coat=.3)
    # 1929 x-ray machine: column, arm, tube housing with glowing glass bulb
    prim("cylinder", (-1.3, .6, 1.2), (.06, .06, 1.2), metal, vertices=24)
    rbox((-1.3, .6, .05), (.6, .6, .1), metal, .02)
    rbox((-.95, .6, 1.55), (.75, .1, .1), metal, .02)
    bulb = prim("uv_sphere", (-.55, .6, 1.5), (.16, .16, .13), mat("bulb", (.6, .8, 1.), .05, trans=.8, emit=0.), sub=1)
    bm_ = bsdf(bulb.data.materials[0]); es = bm_.inputs["Emission Strength"]; bm_.inputs["Emission Color"].default_value = (.5, .75, 1, 1)
    es.default_value = 0; es.keyframe_insert("default_value", frame=1); es.default_value = 2.5; es.keyframe_insert("default_value", frame=F(20.0))
    es.default_value = 10; es.keyframe_insert("default_value", frame=F(21.1)); es.default_value = 2; es.keyframe_insert("default_value", frame=F(21.6))
    prim("cylinder", (-.55, .6, 1.5), (.05, .05, .25), cream, rot=(0, math.pi / 2, 0), vertices=24)
    for x in (-.85, -.25):
        for k in range(6): prim("torus", (x, .6, 1.5), (.05, .05, .05), mat("coil", (.7, .4, .15), .3, metal=1), rot=(0, math.pi / 2, 0), major_radius=1, minor_radius=.2, sub=0).location.x = x + k * .02
    # fluoroscope screen frame, doctor behind it
    S = Vector((.45, .35, 1.32))
    rbox(S, (.75, .05, .85), mat("frame", (.05, .05, .06), .4), .01)
    scr = rbox(S + Vector((0, -.03, 0)), (.66, .01, .76), mat("screen", (.0, .03, .05), .2, emit=.4, emit_col=(.05, .2, .3)), 0)
    prim("cylinder", (S.x, S.y, .5), (.025, .025, .5), metal, vertices=16)
    doc = doctor("Doc", (.45, .62, 0), 0)
    doc.pose(1, uarm_L=(-10, 0, -20), farm_L=(-35, 0, 0)); doc.brows(1, .4); doc.blink([20, 70]); doc.lids(F(21.1), -28); doc.lids(F(21.2), 50); doc.lids(F(21.5), -28)
    imgs, xh, xc = xray_image(S + Vector((0, -.04, -.02)), .55, 1.)
    beat(xh, xh.scale[:], [F(t) for t in heart_beats(18.7, 23.1)], .08)
    for o in imgs + [xh, xc]:
        o.hide_render = True; o.keyframe_insert("hide_render", frame=1); o.hide_render = False; o.keyframe_insert("hide_render", frame=F(19.6)); set_interp(o)
    grow(xc, F(19.6), F(21.0), .0, 1.)
    beat(xh, xh.scale[:], [F(t) for t in heart_beats(18.7, 23.1)], .08)
    # lights + flash
    light('AREA', (1.5, -1.5, 2.5), 80, (.6, .75, 1.), 2., target=(.4, .4, 1.2), name="cool")
    light('AREA', (-1, 2.2, 2.6), 60, (.4, .6, 1.), 1.5, target=(.4, .4, 1.2), name="rimx")
    fl = light('AREA', (.0, -1.2, 1.6), 0, (.7, .85, 1.), 3., target=(.4, .4, 1.3), name="flash")
    for f, e in ((F(21.1), 0), (F(21.15), 4000), (F(21.5), 0)): key(fl.data, f, energy=e)
    cam = Cam(fstop=2.4)
    cam.shot(1, fB - 1, (1.9, -2.2, 1.7), (1.4, -1.6, 1.6), (-.2, .5, 1.35), (0, .5, 1.4), 28, 32)
    cam.shot(fB, fC - 1, (.15, -.75, 1.75), (.0, -.55, 1.68), (-.6, .6, 1.5), (-.6, .6, 1.5), 40, 50, fstop=2.2)
    cam.shot(fC, n, S + Vector((.05, -.85, .05)), S + Vector((0, -.5, .08)), S + Vector((0, 0, .05)), S + Vector((-.03, 0, .1)), 40, 45, fstop=4)
    cam.handheld(.006)


# ------------------------------------------------------------------ scene 6: punished
def scene6():
    n = nframes(6); fB = F(24.7) + 1
    office(red=.4)
    light('AREA', (-.3, -1.2, 2.3), 120, (1, .15, .1), 2, target=(-.5, 0, 1.6), name="redkey")
    boss_ = boss("Boss", (-.45, .1, 0), math.pi / 2 - .3)
    doc = doctor("Doc", (.6, -.1, 0), -math.pi / 2 - .25)
    # boss face goes red
    sb = bsdf(boss_.mats["skin"]).inputs["Base Color"]
    sb.default_value = (.74, .44, .33, 1); sb.keyframe_insert("default_value", frame=1)
    sb.default_value = (.85, .2, .14, 1); sb.keyframe_insert("default_value", frame=F(24.2))
    boss_.brows(1, -1.); boss_.talk(F(23.3), F(24.6), 1.); boss_.talk(F(24.9), F(26.0), .8)
    boss_.pose(1, chest=(10, 0, 0), head=(-8, 0, 0), uarm_R=(-20, 0, -8), farm_R=(-95, 0, 0), uarm_L=(-25, 0, 8), farm_L=(-90, 0, 0))
    boss_.pose(F(23.4), uarm_R=(-75, 0, -10), farm_R=(-15, 0, 0), chest=(16, 0, 0), head=(-12, 0, 0))
    for k, f in enumerate(range(F(23.5), F(24.6), 4)): boss_.pose(f, farm_R=(-10 - 15 * (k % 2), 0, 0), head=(-12 + 4 * (k % 2), 0, 0))
    # points at the door
    boss_.pose(F(24.9), uarm_R=(-80, 0, 40), farm_R=(-5, 0, 0), head=(-5, 25, 0), chest=(8, 0, 0))
    boss_.pose(n, uarm_R=(-80, 0, 42), farm_R=(-5, 0, 0), head=(-5, 25, 0))
    # steam puffs from the boss's ears
    st = mat("steam", (1, 1, 1), .9, alpha=.5, emit=.6)
    bpy.context.view_layer.update()
    hpos = boss_.rig.matrix_world @ Vector((0, 0, 1.72))
    for i in range(8):
        sg = 1 if i % 2 else -1; p0 = hpos + Vector((.06 * sg, .1 * sg, 0))
        p = prim("uv_sphere", p0, (.001,) * 3, st, sub=1)
        f0 = F(23.6) + i * 4
        key(p, f0, location=p0, scale=(.001,) * 3); key(p, f0 + 14, location=p0 + Vector((.08 * sg, .12 * sg, .18)), scale=(.05,) * 3); key(p, f0 + 22, scale=(.001,) * 3)
    # doctor head down, ashamed
    doc.pose(1, head=(5, 0, 0), chest=(4, 0, 0), uarm_L=(0, 0, -4), uarm_R=(0, 0, 4))
    doc.pose(F(24.8), head=(28, 0, 0), chest=(12, 0, 0)); doc.pose(n, head=(30, 0, 0), chest=(13, 0, 0))
    doc.brows(1, .6); doc.brows(F(24.8), 1.); doc.lids(1, -28); doc.lids(F(24.9), 0); doc.mouth(1, 0, .8)
    cam = Cam(fstop=1.8)
    cam.shot(1, fB - 1, (.15, -.85, 1.6), (.05, -.62, 1.66), (-.45, .1, 1.68), (-.45, .1, 1.7), 32, 36)
    cam.shot(fB, n, (1.1, -1.4, 2.6), (1.0, -1.2, 2.45), (.5, 0, 1.3), (.5, -.05, 1.35), 30, 34, fstop=2.6)
    cam.handheld(.015)


# ------------------------------------------------------------------ scene 7: Nobel
def scene7():
    n = nframes(7); fB = F(28.3) + 1
    world_color((.005, .01, .03), 1.)
    gold = mat("gold", (1., .72, .3), .16, metal=1., bump=.15, bump_scale=300)
    # medal macro set
    M = Vector((40, 0, 1.0))
    med = empty("medal", M)
    disc = prim("cylinder", (0, 0, 0), (.1, .1, .008), gold, rot=(math.pi / 2, 0, 0), vertices=96); disc.parent = med; disc.location = (0, 0, 0)
    rim = prim("torus", (0, 0, 0), (.1, .1, .1), gold, rot=(math.pi / 2, 0, 0), major_radius=1, minor_radius=.06, sub=1, major_segments=96); rim.parent = med; rim.location = (0, 0, 0)
    prof = prim("uv_sphere", (0, 0, 0), (.035, .012, .045), gold, sub=1); prof.parent = med; prof.location = (-.01, -.008, .015)
    t = text("1956", (0, 0, 0), .028, gold, extrude=.002); t.parent = med; t.location = (0, -.009, -.045)
    t2 = text("NOBEL", (0, 0, 0), .018, gold, extrude=.0015); t2.parent = med; t2.location = (0, -.009, .072)
    key(med, 1, rotation_euler=(0, 0, math.radians(-60))); key(med, fB - 1, rotation_euler=(0, 0, math.radians(35)))
    rib = curve_tube([M + Vector((0, .01, .1)), M + Vector((.05, .02, .3)), M + Vector((.1, .03, .6))], .02, mat("ribbon", (.15, .25, .7), .5, sheen=.6), "ribbon")
    rib.data.bevel_depth = 0; rib.data.extrude = .025
    light('AREA', M + Vector((-.4, -.5, .4)), 40, (1, .9, .75), .6, target=M)
    light('AREA', M + Vector((.5, -.3, -.1)), 15, (.6, .7, 1.), .5, target=M)
    light('AREA', M + Vector((0, .4, .3)), 30, (1, 1, 1), .3, target=M)
    rnd = random.Random(9)
    sp = mat("sparkle", (1, .85, .5), emit=20)
    for i in range(40):
        p = M + Vector((rnd.uniform(-.35, .35), rnd.uniform(-.1, .4), rnd.uniform(-.4, .4)))
        o = prim("ico_sphere", p, (.002,) * 3, sp, subdivisions=1, smooth=False)
        f0 = rnd.randint(1, fB - 10); key(o, 1, scale=(0, 0, 0)); key(o, f0, scale=(0, 0, 0)); key(o, f0 + 5, scale=(.003,) * 3); key(o, f0 + 14, scale=(0, 0, 0))
    # stage set
    S = Vector((0, 0, 0))
    rbox(S + Vector((0, 0, .25)), (6, 3, .5), mat("stage", (.2, .08, .05), .2, coat=.8), .02)
    curtain = mat("curtain", (.5, .03, .05), .55, sheen=.8)
    bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=120, y_segments=4, size=1.)
    for v in bm.verts: v.co = Vector((v.co.x * 4, .08 * math.sin(v.co.x * 40) , (v.co.y + 1) * 2.2 + .5))
    me = bpy.data.meshes.new("curtain"); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    cu = bpy.data.objects.new("curtain", me); link(cu); cu.location = (0, 1.4, 0); me.materials.append(curtain)
    text("NOBEL PRIZE  1956", (0, 1.25, 3.4), .32, mat("banner", (1., .78, .35), .2, metal=1., emit=.6, emit_col=(1, .7, .3)), extrude=.03)
    old = doctor("Old", (0, 0, .5), 0, old=True)
    hm = empty("handmedal", (0, 0, 0))
    m2 = prim("cylinder", (0, 0, 0), (.05, .05, .006), gold, rot=(math.pi / 2, 0, 0), vertices=64)
    bpy.context.view_layer.update()
    m2.location = Vector(JOINTS["hd.R"]) + Vector((0, -.03, -.02)); old.attach(m2, "hand.R", rest_space=True)
    old.pose(fB, uarm_R=(-20, 0, 8), farm_R=(-40, 0, 0), head=(0, 0, 0))
    old.pose(F(28.8), uarm_R=(-100, 0, 30), farm_R=(-40, 0, 0), head=(-8, 0, 0), uarm_L=(-10, 0, -10))
    old.pose(n, uarm_R=(-110, 0, 32), farm_R=(-35, 0, 0), head=(-10, 0, 0))
    old.mouth(fB, .3, 1.5); old.brows(fB, .5); old.lids(fB, -18); old.blink([F(29.3)])
    for f in (fB, n):
        old.pose(f, chest=(-4, 0, 0))
    spot = light('SPOT', (0, -2.5, 5.5), 2500, (1, .92, .8), .3, target=(0, 0, 1.4), spot=math.radians(22), name="spot")
    light('AREA', (0, 1.0, 3.5), 300, (1, .8, .5), 2, target=(0, 0, 1.4), name="back")
    light('AREA', (3, -2, 2), 100, (.5, .6, 1.), 2, target=(0, 0, 1.4), name="cfill")
    # confetti
    cm = [mat(f"conf{i}", c, .3, metal=.6, emit=.3) for i, c in enumerate(((1, .75, .25), (1, 1, 1), (.9, .2, .25), (.25, .45, 1)))]
    for i in range(110):
        p = Vector((rnd.uniform(-2.2, 2.2), rnd.uniform(-1.8, .9), rnd.uniform(2.5, 5.)))
        o = prim("plane", p, (.018, .01, 1), rnd.choice(cm), smooth=False)
        dz = rnd.uniform(1.8, 3.); r0 = Euler((rnd.random() * 6, rnd.random() * 6, 0))
        key(o, fB, location=p, rotation_euler=r0)
        key(o, n, location=p + Vector((rnd.uniform(-.3, .3), 0, -dz)), rotation_euler=Euler((r0.x + 8, r0.y + 5, 0)))
    cam = Cam(fstop=2.0)
    cam.shot(1, fB - 1, M + Vector((.12, -.3, .03)), M + Vector((-.05, -.24, .0)), M + Vector((0, 0, .0)), M + Vector((0, 0, .0)), 60, 70, fstop=2.8)
    cam.shot(fB, n, (.35, -1.25, 2.1), (.2, -4.2, 2.3), (0, 0, 2.05), (0, 0, 2.0), 35, 32, fstop=3.)


SCENE_FUNCS = [scene1, scene2, scene3, scene4, scene5, scene6, scene7]


def build(i):
    global T0
    T0 = SCENES[i - 1]["t0"]
    reset(nframes(i))
    SCENE_FUNCS[i - 1]()
    return bpy.context.scene


if __name__ == "__main__":
    i = int(sys.argv[1]); mode = sys.argv[2]
    sc = build(i)
    if mode == "render":
        out = os.path.join(ROOT, "renders", "b3d", f"s{i}")
        f0 = int(sys.argv[3]) if len(sys.argv) > 3 else None; f1 = int(sys.argv[4]) if len(sys.argv) > 4 else None
        render(out, f0, f1)
    elif mode == "still":
        still(sys.argv[4], F(float(sys.argv[3])))
    elif mode == "stills":
        for t in sys.argv[3].split(","): still(f"{sys.argv[4]}_{t}.png", F(float(t)))
    elif mode == "save":
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scenes", f"b3d_s{i}.blend"))
