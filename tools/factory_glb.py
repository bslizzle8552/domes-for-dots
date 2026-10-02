"""Small deterministic glTF 2.0 backend: original rigid-skinned stylized geometry.

No modeling application, network call, or image reconstruction is performed.
Joint transforms and inverse bind matrices are real glTF skinning; clips animate
that skin. This backend intentionally has no arbitrary-rig retargeting claim.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import struct

SEMANTICS = ("idle", "walk", "interact", "sit", "work", "read", "build", "inspect", "garden", "sleep", "talk", "phone")


class GLB:
    def __init__(self):
        self.data = bytearray()
        self.doc = {"asset": {"version": "2.0", "generator": "Domes procedural-rigid-skin/1"},
                    "scene": 0, "scenes": [{"nodes": [0]}], "nodes": [{"name": "Character", "children": []}],
                    "buffers": [], "bufferViews": [], "accessors": [], "materials": [], "meshes": [], "skins": [], "animations": []}

    def accessor(self, rows, kind, component=5126, target=None):
        widths = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}
        width = widths[kind]
        values = [n for row in rows for n in (row if isinstance(row, (list, tuple)) else [row])]
        while len(self.data) % 4:
            self.data.append(0)
        offset = len(self.data)
        formats = {5126: "f", 5123: "H", 5125: "I"}
        self.data.extend(struct.pack("<" + formats[component] * len(values), *values))
        view = {"buffer": 0, "byteOffset": offset, "byteLength": len(self.data) - offset}
        if target:
            view["target"] = target
        self.doc["bufferViews"].append(view)
        accessor = {"bufferView": len(self.doc["bufferViews"]) - 1, "componentType": component, "count": len(rows), "type": kind}
        if kind != "MAT4":
            accessor["min"] = [min(values[i::width]) for i in range(width)]
            accessor["max"] = [max(values[i::width]) for i in range(width)]
        self.doc["accessors"].append(accessor)
        return len(self.doc["accessors"]) - 1

    def save(self, path):
        self.doc["buffers"] = [{"byteLength": len(self.data)}]
        serialized = json.dumps(self.doc, separators=(",", ":"), allow_nan=False).encode()
        serialized += b" " * (-len(serialized) % 4)
        binary = bytes(self.data) + b"\0" * (-len(self.data) % 4)
        path.write_bytes(struct.pack("<III", 0x46546C67, 2, 28 + len(serialized) + len(binary))
                         + struct.pack("<II", len(serialized), 0x4E4F534A) + serialized
                         + struct.pack("<II", len(binary), 0x004E4942) + binary)


def quaternion(x=0.0, y=0.0, z=0.0):
    x, y, z = [math.radians(v) / 2 for v in (x, y, z)]
    cx, sx, cy, sy, cz, sz = math.cos(x), math.sin(x), math.cos(y), math.sin(y), math.cos(z), math.sin(z)
    return [sx*cy*cz-cx*sy*sz, cx*sy*cz+sx*cy*sz, cx*cy*sz-sx*sy*cz, cx*cy*cz+sx*sy*sz]


def create_character(spec: dict, path: Path) -> dict:
    """Produce a self-contained .glb with skin, bones, materials and 12 clips."""
    glb = GLB()
    d = glb.doc
    factor = spec["appearance"]["height_m"] / 1.6
    joints = [
        ("Root", None, (0, 0, 0)), ("Hips", "Root", (0, .78, 0)),
        ("Spine", "Hips", (0, .12, 0)), ("Chest", "Spine", (0, .18, 0)),
        ("Neck", "Chest", (0, .19, 0)), ("Head", "Neck", (0, .12, 0)),
        ("LeftUpperArm", "Chest", (.24, .02, 0)), ("LeftForearm", "LeftUpperArm", (0, -.27, 0)),
        ("LeftHand", "LeftForearm", (0, -.23, 0)),
        ("RightUpperArm", "Chest", (-.24, .02, 0)), ("RightForearm", "RightUpperArm", (0, -.27, 0)),
        ("RightHand", "RightForearm", (0, -.23, 0)),
        ("LeftThigh", "Hips", (.11, 0, 0)), ("LeftShin", "LeftThigh", (0, -.34, 0)),
        ("LeftFoot", "LeftShin", (0, -.34, 0)),
        ("RightThigh", "Hips", (-.11, 0, 0)), ("RightShin", "RightThigh", (0, -.34, 0)),
        ("RightFoot", "RightShin", (0, -.34, 0)),
    ]
    node_ids, globals_, joint_ids = {}, {}, {}
    for name, parent, local in joints:
        node_id = len(d["nodes"])
        node_ids[name] = node_id
        joint_ids[name] = len(joint_ids)
        local = [v * factor for v in local]
        origin = globals_.get(parent, [0, 0, 0])
        globals_[name] = [a+b for a, b in zip(origin, local)]
        d["nodes"].append({"name": name, "translation": local, "children": []})
        d["nodes"][node_ids.get(parent, 0)]["children"].append(node_id)
    matrices = []
    for name, _, _ in joints:
        x, y, z = globals_[name]
        matrices.append([1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, -x, -y, -z, 1])
    d["skins"].append({"name": "DomesHumanoid", "skeleton": node_ids["Root"],
                        "joints": list(node_ids.values()), "inverseBindMatrices": glb.accessor(matrices, "MAT4")})
    colors = spec["appearance"]["colors"]
    for name, color in colors.items():
        rgb = [int(color[i:i+2], 16) / 255 for i in (1, 3, 5)]
        d["materials"].append({"name": name, "pbrMetallicRoughness": {"baseColorFactor": [*rgb, 1], "metallicFactor": .15, "roughnessFactor": .72}})
    materials = {item["name"]: index for index, item in enumerate(d["materials"])}
    # Each primitive has rigid weights to one real skeleton joint. This is
    # deliberate for a segmented robot, not smooth organic deformation.
    primitives = []
    def box(joint, center, size, material):
        center = [globals_[joint][i] + center[i]*factor for i in range(3)]
        half = [v*factor/2 for v in size]
        positions, normals, indices = [], [], []
        faces = [(0, 1), (0, -1), (1, 1), (1, -1), (2, 1), (2, -1)]
        for axis, direction in faces:
            u, v = (axis+1) % 3, (axis+2) % 3
            corners = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
            if direction < 0:
                corners.reverse()
            first = len(positions)
            for a, b in corners:
                point, normal = list(center), [0, 0, 0]
                point[axis] += half[axis]*direction
                point[u] += half[u]*a
                point[v] += half[v]*b
                normal[axis] = direction
                positions.append(point)
                normals.append(normal)
            indices.extend([first, first+1, first+2, first, first+2, first+3])
        primitives.append({"attributes": {
            "POSITION": glb.accessor(positions, "VEC3", target=34962),
            "NORMAL": glb.accessor(normals, "VEC3", target=34962),
            "JOINTS_0": glb.accessor([[joint_ids[joint], 0, 0, 0]]*24, "VEC4", 5123, 34962),
            "WEIGHTS_0": glb.accessor([[1, 0, 0, 0]]*24, "VEC4", target=34962)},
            "indices": glb.accessor(indices, "SCALAR", 5123, 34963), "material": materials[material]})
    box("Hips", (0, .015, 0), (.33, .16, .22), "secondary")
    box("Spine", (0, .085, 0), (.36, .3, .23), "primary")
    head_scale = spec["appearance"]["head_scale"]
    box("Head", (0, .045, 0), (.3*head_scale, .31*head_scale, .27*head_scale), "primary")
    box("Head", (0, .055, -.14*head_scale), (.24*head_scale, .1, .02), "visor")
    for eye_x in [-.065, .065]:
        box("Head", (eye_x, .065, -.157*head_scale), (.033, .033, .016), "accent")
    for side in ["Left", "Right"]:
        box(side+"UpperArm", (0, -.125, 0), (.095, .24, .115), "primary")
        box(side+"Forearm", (0, -.105, 0), (.085, .21, .1), "secondary")
        box(side+"Hand", (0, -.035, -.012), (.09, .095, .09), "accent")
        box(side+"Thigh", (0, -.15, 0), (.125, .29, .16), "secondary")
        box(side+"Shin", (0, -.15, 0), (.105, .29, .12), "primary")
        box(side+"Foot", (0, -.05, -.045), (.14, .1, .24), "secondary")
    if spec["appearance"]["clothing"] == "vest":
        box("Chest", (0, -.04, -.126), (.28, .23, .025), "secondary")
    if "chest_badge" in spec["appearance"]["accessories"]:
        box("Chest", (.08, 0, -.15), (.065, .065, .025), "accent")
    if "antenna" in spec["appearance"]["accessories"]:
        box("Head", (0, .24, 0), (.025, .12, .025), "secondary")
        box("Head", (0, .31, 0), (.055, .055, .055), "accent")
    if "backpack" in spec["appearance"]["accessories"]:
        box("Spine", (0, .075, .16), (.25, .25, .12), "secondary")
    d["meshes"].append({"name": "OriginalSegmentedBody", "primitives": primitives})
    d["nodes"][0]["children"].append(len(d["nodes"]))
    d["nodes"].append({"name": "SkinnedBody", "mesh": 0, "skin": 0})
    times = [i/8 for i in range(17)]
    time_accessor = glb.accessor(times, "SCALAR")
    for semantic in SEMANTICS:
        channels, samplers = [], []
        poses = [pose(semantic, t, joints) for t in times]
        for name, _, local in joints:
            rotations = [quaternion(*p[0][name]) for p in poses]
            samplers.append({"input": time_accessor, "output": glb.accessor(rotations, "VEC4"), "interpolation": "LINEAR"})
            channels.append({"sampler": len(samplers)-1, "target": {"node": node_ids[name], "path": "rotation"}})
            if name == "Hips":
                values = [[local[0]*factor, (local[1]+p[1])*factor, local[2]*factor] for p in poses]
                samplers.append({"input": time_accessor, "output": glb.accessor(values, "VEC3"), "interpolation": "LINEAR"})
                channels.append({"sampler": len(samplers)-1, "target": {"node": node_ids[name], "path": "translation"}})
        # Godot's importer recognizes the loop suffix; manifest points to the
        # resulting clip names, verified by the runtime audit.
        d["animations"].append({"name": semantic+"_loop", "samplers": samplers, "channels": channels})
    glb.save(path)
    return {"joint_count": len(joints), "mesh_primitives": len(primitives), "animations": [a["name"] for a in d["animations"]], "vertices": len(primitives)*24}


def pose(action, time, joints):
    angles = {name: [0, 0, 0] for name, _, _ in joints}
    wave = math.sin(time*math.pi)
    fast = math.sin(time*2*math.pi)
    offset = 0.0
    def at(name, x=0, y=0, z=0):
        angles[name] = [x, y, z]
    at("Head", y=wave*4)
    if action == "idle":
        at("Chest", x=wave*1.5)
    elif action == "walk":
        at("LeftThigh", x=fast*24)
        at("RightThigh", x=-fast*24)
        at("LeftShin", x=-max(0, -fast)*24)
        at("RightShin", x=-max(0, fast)*24)
        at("LeftUpperArm", x=-fast*25)
        at("RightUpperArm", x=fast*25)
        offset = .015*abs(fast)
    elif action == "sit":
        for side in ["Left", "Right"]:
            at(side+"Thigh", x=90)
            at(side+"Shin", x=-90)
            at(side+"UpperArm", x=15)
        offset = -.34
    elif action == "sleep":
        # Grounded seated doze: no fabricated bed alignment or seat IK.
        for side in ["Left", "Right"]:
            at(side+"Thigh", x=90)
            at(side+"Shin", x=-90)
            at(side+"UpperArm", x=25)
        offset = -.34
        at("Head", x=24+wave*2)
        at("Chest", x=10)
    elif action == "phone":
        at("RightUpperArm", x=20, z=-35)
        at("RightForearm", x=150)
        at("Head", z=-8+wave*2)
    elif action in ("work", "build", "read"):
        for side, sign in [("Left", 1), ("Right", -1)]:
            at(side+"UpperArm", x=45+(fast*8*sign if action != "read" else 0))
            at(side+"Forearm", x=35+(fast*16*sign if action == "build" else 0))
        at("Head", x=20+wave*2)
    elif action == "garden":
        at("Chest", x=22)
        at("RightUpperArm", x=40+wave*15)
        at("RightForearm", x=25)
        at("Head", x=20)
    elif action == "inspect":
        at("Head", x=10, y=wave*25)
        at("RightUpperArm", x=35)
        at("RightForearm", x=60)
    elif action == "talk":
        at("Head", x=fast*3, y=wave*8)
        at("LeftUpperArm", x=25, z=15+wave*10)
        at("LeftForearm", x=40)
    else:
        at("RightUpperArm", x=45+wave*8)
        at("RightForearm", x=20)
    return angles, offset


def read_glb(path: Path):
    raw = path.read_bytes()
    if len(raw) < 28 or struct.unpack_from("<III", raw) != (0x46546C67, 2, len(raw)):
        raise ValueError("invalid GLB header or length")
    length, kind = struct.unpack_from("<II", raw, 12)
    if kind != 0x4E4F534A or 20+length+8 > len(raw):
        raise ValueError("missing GLB JSON chunk")
    doc = json.loads(raw[20:20+length])
    binary_length, kind = struct.unpack_from("<II", raw, 20+length)
    if kind != 0x004E4942 or 28+length+binary_length != len(raw):
        raise ValueError("invalid GLB binary chunk")
    return doc, raw[28+length:]


def accessor_values(doc, binary, index):
    accessor = doc["accessors"][index]
    view = doc["bufferViews"][accessor["bufferView"]]
    width = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}[accessor["type"]]
    fmt = {5126: "f", 5123: "H", 5125: "I"}[accessor["componentType"]]
    size = struct.calcsize(fmt)*width
    offset = view.get("byteOffset", 0)+accessor.get("byteOffset", 0)
    if view.get("buffer", 0) != 0 or offset+size*accessor["count"] > view.get("byteOffset", 0)+view["byteLength"] or offset+size*accessor["count"] > len(binary):
        raise ValueError("GLB accessor exceeds its buffer view")
    return [struct.unpack_from("<"+fmt*width, binary, offset+i*size) for i in range(accessor["count"])]
