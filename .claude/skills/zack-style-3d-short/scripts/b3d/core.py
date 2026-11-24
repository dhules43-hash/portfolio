"""Core Blender (bpy 5.x) toolkit for the full-3D Zack-style build: render setup, materials, lights, cameras,
and a rigged smooth-skinned character generator (skin-modifier body + armature + detailed face)."""
import bpy, bmesh, math, os, random
from mathutils import Vector, Matrix, Euler

FPS = 30
RES = (int(os.environ.get("RW", 540)), int(os.environ.get("RH", 960)))
SAMPLES = int(os.environ.get("SAMPLES", 20))


# ---------------------------------------------------------------- scene / render
def reset(n_frames):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    p = bpy.context.preferences.edit
    p.keyframe_new_interpolation_type = 'BEZIER'; p.keyframe_new_handle_type = 'AUTO_CLAMPED'
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; c = sc.cycles
    c.device = 'CPU'; c.samples = SAMPLES; c.use_adaptive_sampling = True; c.adaptive_threshold = .05
    c.use_denoising = True; c.denoiser = 'OPENIMAGEDENOISE'
    c.max_bounces = 5; c.diffuse_bounces = 2; c.glossy_bounces = 2; c.transmission_bounces = 4; c.transparent_max_bounces = 8
    c.caustics_reflective = False; c.caustics_refractive = False; c.blur_glossy = 1.0
    sc.render.use_persistent_data = True
    sc.render.resolution_x, sc.render.resolution_y = RES; sc.render.resolution_percentage = 100
    sc.render.fps = FPS; sc.frame_start = 1; sc.frame_end = n_frames
    sc.render.use_motion_blur = os.environ.get('MBLUR', '0') == '1'; sc.render.motion_blur_shutter = .35
    try: sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Punchy'
    except Exception: pass
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'
    w = bpy.data.worlds.new("World"); sc.world = w
    return sc


def world_color(col, strength=1.0):
    nt = bpy.context.scene.world.node_tree
    bg = next(n for n in nt.nodes if n.type == 'BACKGROUND')
    bg.inputs[0].default_value = (*col, 1); bg.inputs[1].default_value = strength
    return bg


def world_gradient(bottom, top, strength=1.0):
    nt = bpy.context.scene.world.node_tree; nt.nodes.clear()
    tc = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ"); ramp = nt.nodes.new("ShaderNodeValToRGB")
    bg = nt.nodes.new("ShaderNodeBackground"); out = nt.nodes.new("ShaderNodeOutputWorld")
    ramp.color_ramp.elements[0].position = .45; ramp.color_ramp.elements[0].color = (*bottom, 1)
    ramp.color_ramp.elements[1].position = .75; ramp.color_ramp.elements[1].color = (*top, 1)
    nt.links.new(tc.outputs["Generated"], sp.inputs[0]); nt.links.new(sp.outputs["Z"], ramp.inputs[0])
    nt.links.new(ramp.outputs[0], bg.inputs[0]); nt.links.new(bg.outputs[0], out.inputs[0]); bg.inputs[1].default_value = strength


def render(outdir, f0=None, f1=None):
    sc = bpy.context.scene; os.makedirs(outdir, exist_ok=True)
    if f0: sc.frame_start = f0
    if f1: sc.frame_end = f1
    sc.render.filepath = os.path.join(outdir, "")
    sc.render.use_overwrite = False; sc.render.use_placeholder = True
    bpy.ops.render.render(animation=True)


def still(path, frame):
    sc = bpy.context.scene; sc.frame_set(frame); sc.render.filepath = path; bpy.ops.render.render(write_still=True)


# ---------------------------------------------------------------- keyframes
def key(o, frame, **kw):
    for k, v in kw.items():
        setattr(o, k, v); o.keyframe_insert(k, frame=frame)


def sec(t):
    return int(round(t * FPS)) + 1


# ---------------------------------------------------------------- materials
def mat(name, col, rough=.45, metal=0., sss=0., sss_rad=(1., .35, .2), coat=0., emit=0., emit_col=None,
        alpha=1., trans=0., bump=0., bump_scale=180., spec=.5, sheen=0.):
    m = bpy.data.materials.new(name)
    try: m.use_nodes = True
    except Exception: pass
    nt = m.node_tree; b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'); I = b.inputs
    I["Base Color"].default_value = (*col, 1); I["Roughness"].default_value = rough; I["Metallic"].default_value = metal
    if sss: I["Subsurface Weight"].default_value = sss; I["Subsurface Radius"].default_value = sss_rad; I["Subsurface Scale"].default_value = .03
    if coat: I["Coat Weight"].default_value = coat; I["Coat Roughness"].default_value = .08
    if emit: I["Emission Color"].default_value = (*(emit_col or col), 1); I["Emission Strength"].default_value = emit
    if trans: I["Transmission Weight"].default_value = trans
    if sheen: I["Sheen Weight"].default_value = sheen
    if alpha < 1: I["Alpha"].default_value = alpha
    if bump:
        n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = bump_scale; n.inputs["Detail"].default_value = 6
        bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; bp.inputs["Distance"].default_value = .002
        nt.links.new(n.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], I["Normal"])
    return m


def bsdf(m):
    return next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')


def skin_mat(name="skin", col=(.78, .5, .38), rough=.42):
    return mat(name, col, rough, sss=.18, bump=.25, bump_scale=260)


# ---------------------------------------------------------------- objects
def link(o, coll=None):
    (coll or bpy.context.scene.collection).objects.link(o); return o


def prim(kind, loc=(0, 0, 0), scale=(1, 1, 1), m=None, rot=(0, 0, 0), smooth=True, sub=0, name=None, **kw):
    getattr(bpy.ops.mesh, f"primitive_{kind}_add")(location=loc, rotation=rot, **kw)
    o = bpy.context.object; o.scale = scale
    if m: o.data.materials.append(m)
    if smooth: o.data.shade_smooth() if hasattr(o.data, "shade_smooth") else bpy.ops.object.shade_smooth()
    if sub: md = o.modifiers.new("sub", 'SUBSURF'); md.levels = sub; md.render_levels = sub
    if name: o.name = name
    return o


def rbox(loc, size, m, bevel=.02, rot=(0, 0, 0), name=None):
    """Rounded box (bevelled) - furniture, walls, props."""
    o = prim("cube", loc, (size[0] / 2, size[1] / 2, size[2] / 2), m, rot, smooth=False, name=name)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        b = o.modifiers.new("bev", 'BEVEL'); b.width = bevel; b.segments = 3; b.limit_method = 'ANGLE'
        o.data.shade_smooth() if hasattr(o.data, "shade_smooth") else None
        try: o.data.set_sharp_from_angle(angle=math.radians(40))
        except Exception: pass
    return o


def empty(name, loc=(0, 0, 0), parent=None):
    e = bpy.data.objects.new(name, None); link(e); e.location = loc
    if parent: e.parent = parent
    return e


def curve_tube(points, radius, m, name="tube", res=8, taper_end=False):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = radius; cu.bevel_resolution = res
    cu.use_fill_caps = True; cu.resolution_u = 24
    sp = cu.splines.new('BEZIER'); sp.bezier_points.add(len(points) - 1)
    for bp, c in zip(sp.bezier_points, points):
        bp.co = c; bp.handle_left_type = bp.handle_right_type = 'AUTO'
    o = bpy.data.objects.new(name, cu); link(o); o.data.materials.append(m)
    return o


def grow(curve_obj, f0, f1, start=0., end=1.):
    """Animate a curve 'growing' along its length (catheter insertion etc.)."""
    d = curve_obj.data; d.bevel_factor_mapping_end = 'SPLINE'
    d.bevel_factor_end = start; d.keyframe_insert("bevel_factor_end", frame=f0)
    d.bevel_factor_end = end; d.keyframe_insert("bevel_factor_end", frame=f1)


# ---------------------------------------------------------------- lights
def light(kind, loc, energy, color=(1, 1, 1), size=1., rot=None, target=None, name="L", spot=None):
    d = bpy.data.lights.new(name, kind); d.energy = energy; d.color = color
    if kind == 'AREA': d.size = size
    if kind in ('POINT', 'SPOT'): d.shadow_soft_size = size
    if kind == 'SUN': d.angle = size
    if kind == 'SPOT' and spot: d.spot_size = spot; d.spot_blend = .4
    o = bpy.data.objects.new(name, d); link(o); o.location = loc
    if rot: o.rotation_euler = rot
    if target is not None: aim(o, target)
    return o


def aim(o, target):
    d = Vector(target) - Vector(o.location)
    o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def three_point(c, key=260, fill=70, rim=220, warm=(1, .9, .78), cool=(.75, .85, 1), scale=1.):
    c = Vector(c)
    light('AREA', c + Vector((-2.2, -2.6, 2.4)) * scale, key * scale ** 2, warm, 2.5 * scale, target=c, name="key")
    light('AREA', c + Vector((2.8, -2.2, .9)) * scale, fill * scale ** 2, cool, 3 * scale, target=c, name="fill")
    light('AREA', c + Vector((.6, 2.8, 2.6)) * scale, rim * scale ** 2, (1, .97, .92), 1.5 * scale, target=c, name="rim")


# ---------------------------------------------------------------- camera
class Cam:
    """Camera + look-at target + DOF. shot() keys a move; consecutive shots = hard cut."""
    def __init__(self, name="cam", fstop=2.0, sensor=36):
        self.d = bpy.data.cameras.new(name); self.d.sensor_fit = 'VERTICAL'; self.d.sensor_height = sensor
        self.d.dof.use_dof = True; self.d.dof.aperture_fstop = fstop; self.d.clip_start = .005; self.d.clip_end = 300
        self.o = bpy.data.objects.new(name, self.d); link(self.o); bpy.context.scene.camera = self.o
        self.t = empty(name + "_tgt"); self.d.dof.focus_object = self.t
        c = self.o.constraints.new('TRACK_TO'); c.target = self.t; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
        self.shake = None

    def shot(self, f0, f1, p0, p1, t0, t1, lens0=35, lens1=None, fstop=None):
        lens1 = lens1 or lens0
        key(self.o, f0, location=p0); key(self.t, f0, location=t0); self.d.lens = lens0; self.d.keyframe_insert("lens", frame=f0)
        key(self.o, f1, location=p1); key(self.t, f1, location=t1); self.d.lens = lens1; self.d.keyframe_insert("lens", frame=f1)
        if fstop:
            self.d.dof.aperture_fstop = fstop; self.d.dof.keyframe_insert("aperture_fstop", frame=f0)

    def handheld(self, amount=.004, speed=.6):
        """Subtle handheld drift via noise modifiers on the target."""
        ad = self.t.animation_data
        if not ad or not ad.action: return
        for fc in fcurves(ad.action):
            if fc.data_path == "location":
                n = fc.modifiers.new('NOISE'); n.scale = 40 / speed; n.strength = amount * 2; n.phase = random.random() * 50


def fcurves(action):
    """bpy 4.4+/5.x layered actions vs legacy."""
    if hasattr(action, "fcurves") and action.fcurves is not None:
        try: return list(action.fcurves)
        except Exception: pass
    out = []
    for layer in getattr(action, "layers", []):
        for strip in layer.strips:
            for cb in strip.channelbags: out += list(cb.fcurves)
    return out


def all_fcurves(o):
    ad = getattr(o, "animation_data", None)
    return fcurves(ad.action) if ad and ad.action else []


def set_interp(o, kind='CONSTANT'):
    for fc in all_fcurves(o):
        for kp in fc.keyframe_points: kp.interpolation = kind


# ---------------------------------------------------------------- character
# Rest pose (A-pose), metres, character faces -Y. L = +X.
JOINTS = {
    "pelvis": (0, 0, .96), "spine": (0, 0, 1.12), "chest": (0, 0, 1.33), "neck": (0, 0, 1.5), "headb": (0, 0, 1.58), "headt": (0, 0, 1.8),
    "sh.L": (.2, 0, 1.44), "el.L": (.27, .02, 1.17), "wr.L": (.31, -.01, .94), "hd.L": (.325, -.02, .86),
    "hp.L": (.095, 0, .93), "kn.L": (.105, -.01, .5), "an.L": (.105, .02, .085), "to.L": (.105, -.11, .03),
}
for k, v in list(JOINTS.items()):
    if k.endswith(".L"): JOINTS[k[:-2] + ".R"] = (-v[0], v[1], v[2])

BONES = [  # name, head joint, tail joint, parent
    ("pelvis", "pelvis", "spine", None), ("spine", "spine", "chest", "pelvis"), ("chest", "chest", "neck", "spine"),
    ("neck", "neck", "headb", "chest"), ("head", "headb", "headt", "neck"),
]
for s in ("L", "R"):
    BONES += [(f"clav.{s}", "chest", f"sh.{s}", "chest"), (f"uarm.{s}", f"sh.{s}", f"el.{s}", f"clav.{s}"),
              (f"farm.{s}", f"el.{s}", f"wr.{s}", f"uarm.{s}"), (f"hand.{s}", f"wr.{s}", f"hd.{s}", f"farm.{s}"),
              (f"thigh.{s}", f"hp.{s}", f"kn.{s}", "pelvis"), (f"shin.{s}", f"kn.{s}", f"an.{s}", f"thigh.{s}"),
              (f"foot.{s}", f"an.{s}", f"to.{s}", f"shin.{s}")]


def _body_mesh(name, build, coat_len=0.):
    """Skeleton graph -> Skin modifier -> Subsurf -> applied mesh with per-region materials."""
    J = {k: Vector(v) for k, v in JOINTS.items()}
    sx = build.get("width", 1.); belly = build.get("belly", 0.)
    verts, radii, edges, tags = [], [], [], []

    def add(p, r, tag):
        verts.append(Vector(p)); radii.append(r); tags.append(tag); return len(verts) - 1

    def chain(pts, rs, tag, start=None):
        idx = [start] if start is not None else []
        for p, r in zip(pts, rs): idx.append(add(p, r, tag))
        for a, b in zip(idx, idx[1:]): edges.append((a, b))
        return idx

    lerp = lambda a, b, t: a + (b - a) * t
    # torso
    tor = chain([J["pelvis"] + Vector((0, 0, -.06)), J["pelvis"], J["spine"], lerp(J["spine"], J["chest"], .55), J["chest"] + Vector((0, 0, .06)), J["neck"], J["headb"]],
                [(.15 * sx, .105), (.165 * sx, .115 + belly * .5), (.15 * sx + belly * .4, .11 + belly), (.165 * sx + belly * .2, .115 + belly * .6), (.18 * sx, .11), (.074, .07), (.068, .066)], "torso")
    chest_i = tor[4]; pelvis_i = tor[1]
    for s in ("L", "R"):
        sg = 1 if s == "L" else -1
        arm = chain([J[f"sh.{s}"] + Vector((-sg * .02, 0, -.01)), J[f"sh.{s}"] + Vector((sg * .015, 0, -.02)), lerp(J[f"sh.{s}"], J[f"el.{s}"], .5), J[f"el.{s}"], lerp(J[f"el.{s}"], J[f"wr.{s}"], .45), J[f"wr.{s}"]],
                    [(.065, .065), (.06, .06), (.052, .052), (.042, .042), (.04, .038), (.03, .022)], "arm", start=chest_i)
        wr = J[f"wr.{s}"]; hd = J[f"hd.{s}"]; dirv = (hd - wr).normalized()
        palm = chain([lerp(wr, hd, .55)], [(.042, .018)], "hand", start=arm[-1])[-1]
        side = Vector((0, -1, 0)).cross(dirv).normalized()
        for k, off in enumerate((-.024, -.008, .008, .024)):
            base = lerp(wr, hd, .6) + side * off * sg
            ln = (.055, .062, .058, .046)[k]
            chain([base + dirv * .03, base + dirv * (.03 + ln * .5), base + dirv * (.03 + ln)], [(.0095, .0085), (.0085, .0078), (.007, .0065)], "hand", start=palm)
        tb = wr + dirv * .035 + Vector((0, -.03, 0))
        chain([tb, tb + dirv * .025 + Vector((0, -.02, 0)), tb + dirv * .045 + Vector((0, -.03, 0))], [(.012, .011), (.01, .009), (.0085, .008)], "hand", start=palm)
        leg = chain([J[f"hp.{s}"] + Vector((0, 0, .02)), lerp(J[f"hp.{s}"], J[f"kn.{s}"], .45), J[f"kn.{s}"], lerp(J[f"kn.{s}"], J[f"an.{s}"], .4), J[f"an.{s}"] + Vector((0, 0, .02))],
                    [(.095, .1), (.075, .078), (.058, .06), (.055, .058), (.042, .044)], "leg", start=tor[0])
        chain([J[f"an.{s}"] + Vector((0, -.03, -.035)), J[f"to.{s}"] + Vector((0, 0, -.002))], [(.05, .04), (.045, .03)], "foot", start=leg[-1])
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in verts], edges, [])
    o = bpy.data.objects.new(name, me); link(o)
    sk = o.modifiers.new("skin", 'SKIN'); sk.use_smooth_shade = True; sk.branch_smoothing = .5
    for i, r in enumerate(radii): me.skin_vertices[0].data[i].radius = r
    me.skin_vertices[0].data[pelvis_i].use_root = True
    ss = o.modifiers.new("sub", 'SUBSURF'); ss.levels = 2
    bpy.context.view_layer.objects.active = o; o.select_set(True)
    bpy.ops.object.modifier_apply(modifier="skin"); bpy.ops.object.modifier_apply(modifier="sub")
    o.select_set(False)
    return o


def _assign_body_materials(o, mats, outfit):
    """Region by rest position: head/neck/hands = skin, torso+arms = top, legs = bottoms, feet = shoes."""
    me = o.data
    names = ["skin", "top", "bottom", "shoes", "sleeve2"]
    for n in names: me.materials.append(mats.get(n, mats["top"]))
    J = {k: Vector(v) for k, v in JOINTS.items()}
    sleeve = outfit.get("sleeve", 1.0)  # 1 = to wrist, .5 = short sleeve
    for p in me.polygons:
        c = p.center; idx = 1
        ax = abs(c.x)
        on_arm = ax > .17 and c.z > .8 and c.z < 1.5 and not (ax < .2 and c.z > 1.36)
        if c.z > 1.47 and ax < .12: idx = 0
        elif on_arm:
            el = J["el.L"]; wr = J["wr.L"]
            if c.z < wr.z + .015: idx = 0
            elif sleeve < 1 and c.z < el.z + (1 - sleeve) * .25: idx = 0
            else: idx = 1
        elif c.z < .16 and (c.z < .12 or c.y < -.02): idx = 3
        elif c.z < J["pelvis"].z - .04 + outfit.get("top_drop", 0):
            idx = 2
        p.material_index = idx


def parent_to_bone(o, rig, bone):
    """Bone-parent keeping the current world transform (rig must be in rest pose at creation time)."""
    bpy.context.view_layer.update()
    pb = rig.pose.bones[bone]
    pm = rig.matrix_world @ pb.matrix @ Matrix.Translation((0, pb.length, 0))
    mw = o.matrix_world.copy()
    o.parent = rig; o.parent_type = 'BONE'; o.parent_bone = bone
    o.matrix_parent_inverse = pm.inverted()
    o.matrix_basis = mw
    return o


def make_armature(name, build_scale=1.0):
    arm = bpy.data.armatures.new(name + "_arm"); o = bpy.data.objects.new(name + "_rig", arm); link(o)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.mode_set(mode='EDIT')
    eb = {}
    for bn, h, t, par in BONES:
        b = arm.edit_bones.new(bn); b.head = JOINTS[h]; b.tail = JOINTS[t]
        if bn.startswith(("uarm", "farm", "hand")): b.roll = 0
        if par: b.parent = eb[par]; b.use_connect = False
        eb[bn] = b
    bpy.ops.object.mode_set(mode='OBJECT')
    for pb in o.pose.bones: pb.rotation_mode = 'XYZ'
    return o


def _seg_dist(p, a, b):
    ab = b - a; t = max(0., min(1., (p - a).dot(ab) / ab.length_squared)); return (a + ab * t - p).length


def _weights(body, rig):
    """Region-aware nearest-bone weights (robust replacement for heat weighting)."""
    J = {k: Vector(v) for k, v in JOINTS.items()}
    segs = {bn: (J[h], J[t]) for bn, h, t, _ in BONES}
    groups = {bn: body.vertex_groups.new(name=bn) for bn, *_ in BONES}
    for v in body.data.vertices:
        p = v.co; ax = abs(p.x); s = "L" if p.x > 0 else "R"
        if p.z > 1.47 and ax < .12: cand = ["neck", "head", "chest"] if p.z < 1.6 else ["head"]
        elif ax > .16 and p.z > .78 and p.z < 1.52 and not (ax < .21 and p.z > 1.38) and p.z > J[f"wr.{s}"].z - .2:
            cand = [f"clav.{s}", f"uarm.{s}", f"farm.{s}", f"hand.{s}", "chest"]
        elif p.z < .98 and ax > .015 and p.z < J["pelvis"].z - .02:
            cand = [f"thigh.{s}", f"shin.{s}", f"foot.{s}", "pelvis"]
        else: cand = ["pelvis", "spine", "chest", "neck", f"clav.{s}"]
        ds = sorted((_seg_dist(p, *segs[c]), c) for c in cand)
        d0 = ds[0][0]; ws = [(math.exp(-((d - d0) / .035) ** 2), c) for d, c in ds[:3]]
        tot = sum(w for w, _ in ws)
        for w, c in ws:
            if w / tot > .02: groups[c].add([v.index], w / tot, 'REPLACE')


def _head(name, rig, build, mats):
    """Detailed head parts, bone-parented to 'head'. Returns dict of animatable parts."""
    hb = Vector(JOINTS["headb"]); C = hb + Vector((0, -.008, .118 * build.get("head", 1.0) * 1.14 - .03))
    hs = build.get("head", 1.0) * 1.14
    parts = {}

    def bone_parent(o):
        return parent_to_bone(o, rig, "head")

    def local(p):
        return C + Vector(p) * hs

    # skull+face as one sculpted mesh
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=32, radius=1.)
    jaw = build.get("jaw", 1.); chub = build.get("chub", 0.)
    for v in bm.verts:
        x, y, z = v.co
        sx, sy, sz = .092, .108, .122
        if z < 0:                                     # narrow lower face -> jaw & chin
            k = -z
            sx *= 1 - .28 * k ** 1.6 * (1.2 - .2 * jaw) + chub * .2 * k; sy *= 1 - .05 * k
            if y < 0: sy *= 1 + .1 * k * (1 if jaw > 1 else .6)
        if y > .3: sy *= 1 + .08 * (y - .3)            # back of skull
        if y < -.6 and abs(z) < .35: sy *= 1 - .07 * (1 - abs(z) / .35) * (-y - .6) / .4   # flatten face plane
        brow = math.exp(-((z - .22) / .12) ** 2) * math.exp(-(x / .55) ** 2) * max(0, -y) ** 3
        cheek = math.exp(-((z + .2) / .18) ** 2) * math.exp(-((abs(x) - .45) / .2) ** 2) * max(0, -y)
        socket = math.exp(-((z - .08) / .1) ** 2) * math.exp(-((abs(x) - .36) / .14) ** 2) * max(0, -y) ** 2
        v.co = Vector((x * sx, y * sy * (1 + .07 * brow + .05 * cheek * (1 + chub * 3) - .09 * socket), z * sz))
    me = bpy.data.meshes.new(name + "_head"); bm.to_mesh(me); bm.free()
    head = bpy.data.objects.new(name + "_head", me); link(head); head.location = C
    head.scale = (hs, hs, hs); me.materials.append(mats["skin"]); me.shade_smooth() if hasattr(me, "shade_smooth") else None
    for p in me.polygons: p.use_smooth = True
    md = head.modifiers.new("sub", 'SUBSURF'); md.levels = 1; md.render_levels = 2
    bone_parent(head); parts["head"] = head

    def part(kind, p, s, m, rot=(0, 0, 0), sub=1, **kw):
        o = prim(kind, local(p), tuple(x * hs for x in s), m, rot, sub=sub, **kw); bone_parent(o); return o

    # nose
    nb = build.get("nose", 1.) * .85
    part("uv_sphere", (0, -.104, -.01), (.017 * nb, .022 * nb, .03 * nb), mats["skin"], rot=(math.radians(-12), 0, 0))
    part("uv_sphere", (0, -.113, -.032), (.016 * nb, .016 * nb, .013 * nb), mats["skin"])
    for sg in (-1, 1): part("uv_sphere", (sg * .014 * nb, -.104, -.036), (.01 * nb, .011, .008), mats["skin"])
    # ears
    for sg in (-1, 1): part("uv_sphere", (sg * .093, .005, .0), (.012, .024, .036), mats["skin"], rot=(0, 0, sg * .3))
    # eyes
    eye_m = mat("eyewhite", (.92, .9, .88), .08, coat=1., sss=.05)
    iris_m = mat("iris", build.get("iris", (.18, .32, .55)), .15, coat=1.)
    pup_m = mat("pupil", (.005, .005, .005), .05, coat=1.)
    parts["eyes"] = []; parts["lids"] = []
    for sg in (-1, 1):
        ep = (sg * .036, -.083, .028)
        e = part("uv_sphere", ep, (.0175, .0175, .0175), eye_m, segments=32, ring_count=16)
        ir = prim("uv_sphere", (0, 0, 0), (.0085 * hs, .0035 * hs, .0085 * hs), iris_m, segments=24, ring_count=12, sub=1)
        ir.parent = e; ir.matrix_parent_inverse = Matrix.Identity(4); ir.location = (0, -.86, 0); ir.scale = (.5, .2, .5)
        pu = prim("uv_sphere", (0, 0, 0), (1, 1, 1), pup_m, segments=16, ring_count=8)
        pu.parent = ir; pu.location = (0, -.55, 0); pu.scale = (.45, .6, .45)
        parts["eyes"].append(e)
        # upper lid: hemisphere shell rotating down for blinks
        bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=1.)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -.05], context='VERTS')
        me = bpy.data.meshes.new("lid"); bm.to_mesh(me); bm.free()
        lid = bpy.data.objects.new("lid", me); link(lid); me.materials.append(mats["skin"])
        for p in me.polygons: p.use_smooth = True
        lid.location = local(ep); lid.scale = (.0195 * hs,) * 3; bone_parent(lid)
        sol = lid.modifiers.new("sol", 'SOLIDIFY'); sol.thickness = .12
        lid.rotation_euler = (math.radians(build.get("lid", -28)), 0, 0)
        parts["lids"].append(lid)
        # lower lid
        lo = part("uv_sphere", (ep[0], ep[1] + .002, ep[2] - .016), (.019, .014, .006), mats["skin"])
    # brows
    hair_m = mats["hair"]; parts["brows"] = []
    for sg in (-1, 1):
        b = part("uv_sphere", (sg * .037, -.094, .056), (.022, .006, .0055), hair_m, rot=(0, sg * math.radians(-8), 0))
        parts["brows"].append(b)
    # mouth: dark interior + lips
    mouth_m = mat("mouth", (.12, .02, .03), .5)
    parts["mouth"] = part("uv_sphere", (0, -.096, -.062), (.022, .01, .004), mouth_m)
    lip_m = mat("lip", tuple(c * .85 for c in mats["skin_col"]) if "skin_col" in mats else (.65, .35, .3), .35, sss=.2)
    lip_m = mats.get("lip", lip_m)
    parts["ulip"] = part("uv_sphere", (0, -.1, -.055), (.023, .009, .0055), lip_m)
    parts["llip"] = part("uv_sphere", (0, -.098, -.07), (.021, .009, .0065), lip_m)
    # hair
    style = build.get("hair", "short")
    if style != "bald":
        bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=24, radius=1.)
        cut = {"short": -.05, "side": -.3, "comb": -.02}[style]
        rng = random.Random(7)
        for v in bm.verts:
            x, y, z = v.co
            v.co = Vector((x * .095, y * .113, z * .127))
        kill = [v for v in bm.verts if (v.co.z / .133) < cut + (.55 if v.co.y < 0 else 0) * max(0, -v.co.y / .118) ** 1.5
                or (style == "side" and (v.co.z / .127 > .38 or v.co.y / .113 < -.35))]
        bmesh.ops.delete(bm, geom=kill, context='VERTS')
        me = bpy.data.meshes.new("hair"); bm.to_mesh(me); bm.free()
        h = bpy.data.objects.new(name + "_hair", me); link(h); me.materials.append(hair_m)
        for p in me.polygons: p.use_smooth = True
        h.location = local((0, .004, .003)); h.scale = (hs,) * 3; bone_parent(h)
        sol = h.modifiers.new("sol", 'SOLIDIFY'); sol.thickness = .008; sol.offset = 1
        dsp = h.modifiers.new("dsp", 'DISPLACE'); tx = bpy.data.textures.new('hairtex', 'CLOUDS'); tx.noise_scale = .02; dsp.texture = tx; dsp.strength = .004; dsp.mid_level = .5
        s2 = h.modifiers.new("sub", 'SUBSURF'); s2.levels = 1; s2.render_levels = 2
        parts["hair"] = h
    if build.get("mustache"):
        part("uv_sphere", (0, -.108, -.045), (.03, .01, .008), hair_m, rot=(0, 0, 0))
    if build.get("glasses"):
        gm = mat("glassframe", (.05, .05, .05), .2, metal=.8)
        for sg in (-1, 1):
            r = part("torus", (sg * .036, -.112, .03), (.019, .019, .019), gm, rot=(math.pi / 2, 0, 0), major_radius=1, minor_radius=.1, sub=0)
    return parts


class Character:
    def __init__(self, name, loc=(0, 0, 0), yaw=0., scale=1., build=None, outfit=None):
        build = build or {}; outfit = outfit or {}
        self.name = name
        skin_col = build.get("skin", (.72, .42, .29))
        mats = {"skin": skin_mat(name + "_skin", skin_col), "skin_col": skin_col,
                "top": mat(name + "_top", outfit.get("top", (.92, .92, .9)), .7, sheen=.3, bump=.05, bump_scale=600),
                "bottom": mat(name + "_bottom", outfit.get("bottom", (.18, .2, .26)), .75, sheen=.2),
                "shoes": mat(name + "_shoes", outfit.get("shoes", (.08, .05, .04)), .3, coat=.5),
                "hair": mat(name + "_hair", build.get("hair_col", (.06, .04, .03)), .5, sheen=.4, bump=.4, bump_scale=900)}
        self.mats = mats
        self.rig = make_armature(name)
        self.body = _body_mesh(name + "_body", build)
        _assign_body_materials(self.body, mats, outfit)
        _weights(self.body, self.rig)
        am = self.body.modifiers.new("arm", 'ARMATURE'); am.object = self.rig
        sub = self.body.modifiers.new("sub", 'SUBSURF'); sub.levels = 0; sub.render_levels = 1
        self.body.parent = self.rig
        self.face = _head(name, self.rig, build, mats)
        if outfit.get("tie"):
            t = prim("cone", (0, -.118, 1.3), (.025, .012, .12), mat(name + "_tie", outfit["tie"], .4, sheen=.3), rot=(math.pi, 0, 0), vertices=4, smooth=False)
            self.attach(t, "chest")
        belt = prim("torus", (0, 0, JOINTS["pelvis"][2] - .045), (.168, .118, .11), mat(name + "_belt", outfit.get("belt", (.05, .03, .02)), .35, coat=.4),
                    major_radius=1, minor_radius=.22, sub=1)
        self.attach(belt, "pelvis")
        for s_ in ("L", "R"):
            wr = Vector(JOINTS[f"wr.{s_}"]); el = Vector(JOINTS[f"el.{s_}"]); d = (wr - el).normalized()
            cuff = prim("torus", tuple(wr - d * .02), (.036, .036, .036), mats["top"], major_radius=1, minor_radius=.22, sub=1)
            cuff.rotation_euler = d.to_track_quat('Z', 'Y').to_euler(); self.attach(cuff, f"farm.{s_}")
        if outfit.get("collar", False):
            col = prim("torus", (0, -.004, 1.465), (.078, .072, .07), mats["top"], major_radius=1, minor_radius=.16, sub=1)
            self.attach(col, "chest")
        self.rig.location = loc; self.rig.rotation_euler = (0, 0, yaw); self.rig.scale = (scale,) * 3
        self.pb = self.rig.pose.bones

    def attach(self, o, bone, rest_space=False):
        """Bone-parent o. If rest_space, o is positioned in the character's rest (unrotated, origin) space."""
        bpy.context.view_layer.update()
        saved = self.rig.matrix_world.copy()
        if not rest_space:
            o.matrix_world = saved.inverted() @ o.matrix_world
        self.rig.matrix_world = Matrix.Identity(4)
        saved_pose = {pb.name: pb.matrix_basis.copy() for pb in self.rig.pose.bones}
        for pb in self.rig.pose.bones: pb.matrix_basis = Matrix.Identity(4)
        parent_to_bone(o, self.rig, bone)
        for pb in self.rig.pose.bones: pb.matrix_basis = saved_pose[pb.name]
        self.rig.matrix_world = saved; bpy.context.view_layer.update()
        return o

    # ---- posing
    def pose(self, frame, **rots):
        """rots: bone_name=(x,y,z) degrees (local bone axes). Use '_' instead of '.' e.g. uarm_L."""
        for k, v in rots.items():
            b = self.pb[k.replace("_L", ".L").replace("_R", ".R")]
            b.rotation_euler = tuple(math.radians(a) for a in v); b.keyframe_insert("rotation_euler", frame=frame)

    def move(self, frame, loc=None, yaw=None):
        if loc is not None: key(self.rig, frame, location=loc)
        if yaw is not None: key(self.rig, frame, rotation_euler=(0, 0, yaw))

    def blink(self, frames, base=-28):
        for f in frames:
            for l in self.face["lids"]:
                for df, a in ((0, base), (2, 62), (4, 62), (7, base)):
                    l.rotation_euler = (math.radians(a), 0, 0); l.keyframe_insert("rotation_euler", frame=f + df)

    def lids(self, frame, angle):
        for l in self.face["lids"]:
            l.rotation_euler = (math.radians(angle), 0, 0); l.keyframe_insert("rotation_euler", frame=frame)

    def brows(self, frame, mood=0.):
        """mood: -1 angry (inner down), +1 worried/surprised (up)."""
        for b, sg in zip(self.face["brows"], (-1, 1)):
            ang = (-8 + 14 * mood) if mood >= 0 else (-8 + 24 * mood)
            b.rotation_euler = (0, sg * math.radians(-ang if mood < 0 else ang), 0)
            b.keyframe_insert("rotation_euler", frame=frame)
            b.delta_location = (0, 0, .006 * mood); b.keyframe_insert("delta_location", frame=frame)

    def mouth(self, frame, open_=0., wide=1.):
        m = self.face["mouth"]; base = (.022, .01, .004)
        m.scale = (base[0] * wide, base[1], base[2] + .02 * open_); m.keyframe_insert("scale", frame=frame)
        l = self.face["llip"]; l.delta_location = (0, 0, -.018 * open_); l.keyframe_insert("delta_location", frame=frame)

    def talk(self, f0, f1, energy=1.):
        rnd = random.Random(hash(self.name) & 999)
        f = f0
        while f < f1:
            self.mouth(f, rnd.uniform(.25, 1.) * energy, rnd.uniform(.9, 1.2)); f += rnd.choice((3, 4, 5))
        self.mouth(f1, 0)

    def walk(self, f0, f1, start, end, stride=.62, cadence=1.8, arm=22):
        """Procedural walk along a straight line; keys every 2 frames."""
        start, end = Vector(start), Vector(end); dirv = (end - start)
        yaw = math.atan2(-dirv.x, dirv.y) + math.pi if dirv.length else 0
        n = f1 - f0
        for i in range(0, n + 1, 2):
            f = f0 + i; t = i / FPS; ph = 2 * math.pi * cadence / 2 * t
            s = math.sin(ph); c = math.cos(ph)
            p = start + dirv * (i / n)
            self.move(f, loc=(p.x, p.y, p.z + .015 * abs(math.cos(ph))), yaw=yaw)
            self.pose(f, thigh_L=(-28 * s, 0, 0), thigh_R=(28 * s, 0, 0),
                      shin_L=(max(0, -math.sin(ph - .9)) * 55, 0, 0), shin_R=(max(0, math.sin(ph - .9)) * 55, 0, 0),
                      foot_L=(-10 * c, 0, 0), foot_R=(10 * c, 0, 0),
                      uarm_L=(arm * s, 0, 0), uarm_R=(-arm * s, 0, 0), farm_L=(-15 - 10 * max(0, s), 0, 0), farm_R=(-15 - 10 * max(0, -s), 0, 0),
                      pelvis=(0, 0, 4 * s), chest=(3, 0, -5 * s))


def text(body, loc, size, m, rot=(math.pi / 2, 0, 0), extrude=.01, font="/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf", align='CENTER', bevel=.002):
    cu = bpy.data.curves.new("txt", 'FONT'); cu.body = body; cu.size = size; cu.extrude = extrude; cu.bevel_depth = bevel
    cu.align_x = align; cu.align_y = 'CENTER'
    try: cu.font = bpy.data.fonts.load(font, check_existing=True)
    except Exception: pass
    o = bpy.data.objects.new("txt", cu); link(o); o.location = loc; o.rotation_euler = rot; o.data.materials.append(m); return o


def ghost_mat(name, col=(.55, .8, 1.), alpha=.12, emit=.25):
    """Translucent 'x-ray glass' body material (Zack-style anatomy reveal)."""
    m = bpy.data.materials.new(name)
    try: m.use_nodes = True
    except Exception: pass
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); mix = nt.nodes.new("ShaderNodeMixShader"); tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    em = nt.nodes.new("ShaderNodeEmission"); fr = nt.nodes.new("ShaderNodeLayerWeight"); fr.inputs[0].default_value = .35
    em.inputs[0].default_value = (*col, 1); em.inputs[1].default_value = emit * 6
    mp = nt.nodes.new("ShaderNodeMath"); mp.operation = 'MULTIPLY_ADD'; mp.inputs[1].default_value = 1 - alpha; mp.inputs[2].default_value = alpha
    nt.links.new(fr.outputs["Facing"], mp.inputs[0]); nt.links.new(mp.outputs[0], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1]); nt.links.new(em.outputs[0], mix.inputs[2]); nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return m


def set_all_mats(objs, m):
    for o in objs:
        if o.type in ('MESH', 'CURVE', 'FONT') and o.data:
            o.data.materials.clear(); o.data.materials.append(m)


def char_objects(c):
    return [o for o in bpy.data.objects if o.parent == c.rig or o == c.body or (o.parent and o.parent.parent == c.rig) or (o.parent and o.parent.parent and o.parent.parent.parent == c.rig)]


def doctor(name="Forssmann", loc=(0, 0, 0), yaw=0., old=False):
    b = dict(hair="comb" if not old else "side", hair_col=(.07, .045, .03) if not old else (.72, .72, .74), iris=(.2, .35, .55), jaw=1.05)
    if old: b.update(glasses=True, belly=.02, skin=(.72, .45, .34))
    o = dict(top=(.9, .9, .88), bottom=(.1, .11, .15)) if not old else dict(top=(.03, .03, .035), bottom=(.03, .03, .035), tie=(.9, .9, .9), belt=(.02, .02, .02))
    return Character(name, loc, yaw, build=b, outfit=o)


def boss(name="Boss", loc=(0, 0, 0), yaw=0.):
    return Character(name, loc, yaw, build=dict(hair="side", hair_col=(.68, .68, .7), mustache=True, skin=(.74, .44, .33), belly=.05, jaw=1.25, glasses=True, iris=(.25, .2, .15)),
                     outfit=dict(top=(.035, .038, .05), bottom=(.035, .038, .05), tie=(.45, .04, .05)))
