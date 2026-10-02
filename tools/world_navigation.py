"""Static layered support/connectivity checks for the registered straight-ramp grammar."""
from __future__ import annotations
import copy
import math


def validate_layered_navigation(world, assets, character):
    try:
        from validate_content import NavigationCheck
    except ImportError:
        from .validate_content import NavigationCheck
    errors = []
    levels = {item["id"]: item["elevation"] for item in world.get("levels", [])}
    if len(levels) != len(world.get("levels", [])) or not levels:
        return ["layered world requires unique explicit levels"]
    radius, height = world["navigation"]["character_radius"], character["collision"]["height"]
    navigators = {}
    for level, elevation in levels.items():
        zones = [z for z in world["zones"] if z.get("level_id") == level]
        if not zones:
            errors.append(f"level {level} has no support zones")
            continue
        for zone in zones:
            if not math.isclose(zone["center"][1], elevation, abs_tol=1e-7):
                errors.append(f"zone {zone['id']} elevation disagrees with level {level}")
        subset = copy.deepcopy(world)
        subset["zones"] = zones
        subset["objects"] = []
        for obj in world["objects"]:
            asset = assets.get(obj["asset_id"])
            if not asset or not asset["collision"]["enabled"]:
                continue
            center = obj["position"][1]+asset["collision"]["offset"][1]*asset["scale"][1]*obj["scale"][1]
            half = asset["collision"]["size"][1]*asset["scale"][1]*obj["scale"][1]/2
            if center+half > elevation+.05 and center-half < elevation+height:
                subset["objects"].append(obj)
        navigators[level] = NavigationCheck(subset, assets)
    for zone in world["zones"]:
        if zone.get("level_id") not in levels:
            errors.append(f"zone {zone['id']} references unknown level")
    if errors:
        return errors
    # Layered data cannot introduce unsupported floating/overlapping furniture.
    bounds = []
    for obj in world["objects"]:
        asset = assets[obj["asset_id"]]
        if not asset["collision"]["enabled"]:
            continue
        halfx = asset["footprint"][0]*asset["scale"][0]*obj["scale"][0]/2
        halfz = asset["footprint"][1]*asset["scale"][2]*obj["scale"][2]/2
        angle = math.radians(obj["rotation_y"]+asset["rotation_y"])
        sx = abs(math.cos(angle))*halfx+abs(math.sin(angle))*halfz
        sz = abs(math.sin(angle))*halfx+abs(math.cos(angle))*halfz
        x, y, z = obj["position"]
        top = y+(asset["collision"]["offset"][1]+asset["collision"]["size"][1]/2)*obj["scale"][1]*asset["scale"][1]
        supporters = [level for level, elevation in levels.items() if abs(y-elevation) < 1e-7]
        if not any(all(navigators[level].on_floor(x+dx*sx, z+dz*sz) for dx,dz in [(-1,-1),(-1,1),(1,-1),(1,1)]) for level in supporters):
            errors.append(f"object {obj['id']} footprint is outside support; place the complete footprint on one level")
        bounds.append((obj["id"], x-sx, x+sx, y, top, z-sz, z+sz))
    for index, a in enumerate(bounds):
        for b in bounds[index+1:]:
            if min(a[2],b[2])-max(a[1],b[1]) > 1e-7 and min(a[4],b[4])-max(a[3],b[3]) > 1e-7 and min(a[6],b[6])-max(a[5],b[5]) > 1e-7:
                errors.append(f"objects {a[0]} and {b[0]} collision footprints overlap; move one object clear")
    for index, a in enumerate(world["zones"]):
        for b in world["zones"][index+1:]:
            if a["level_id"] == b["level_id"]:
                continue
            if abs(a["center"][0]-b["center"][0]) < (a["size"][0]+b["size"][0])/2 and abs(a["center"][2]-b["center"][2]) < (a["size"][1]+b["size"][1])/2 and abs(a["center"][1]-b["center"][1]) < height+.2:
                errors.append(f"levels at zones {a['id']} and {b['id']} overlap without character headroom")
    transition_edges = []
    seen = set()
    for transition in world.get("transitions", []):
        tid = transition["id"]
        if tid in seen:
            errors.append("duplicate transition "+tid)
        seen.add(tid)
        source, dest = transition["source_level"], transition["destination_level"]
        if source not in levels or dest not in levels or source == dest:
            errors.append(f"transition {tid} must join distinct existing levels")
            continue
        entry, exit = transition["entry"], transition["exit"]
        dx, dz, rise = exit[0]-entry[0], exit[2]-entry[2], exit[1]-entry[1]
        run = math.hypot(dx, dz)
        if (abs(dx) > 1e-7 and abs(dz) > 1e-7) or run < 1e-7:
            errors.append(f"transition {tid} requires a nonzero cardinal straight ramp")
            continue
        if abs(entry[1]-levels[source]) > 1e-7 or abs(exit[1]-levels[dest]) > 1e-7:
            errors.append(f"transition {tid} endpoint elevation disagrees with source/destination")
        if abs(rise-transition["rise"]) > 1e-7 or abs(run-transition["run"]) > 1e-7 or rise/run > .45:
            errors.append(f"transition {tid} rise/run mismatch or slope exceeds 0.45")
        if transition["width"] < max(2.4, 2*radius+2*world["navigation"]["cell_size"]) or transition["headroom"] < height+.2:
            errors.append(f"transition {tid} width/headroom does not fit character envelope")
        inset = max(1.0, radius+world["navigation"]["cell_size"])
        landings = transition["safe_fallbacks"]
        for level, point, endpoint, sign in zip([source, dest], landings, [entry,exit], [-1,1]):
            nav = navigators[level]
            along = ((point[0]-endpoint[0])*dx+(point[2]-endpoint[2])*dz)/run*sign
            across = abs((point[0]-endpoint[0])*dz-(point[2]-endpoint[2])*dx)/run
            if along < inset-1e-7 or across > 1e-7 or not nav.walkable(point[0], point[2]) or abs(point[1]-levels[level]) > 1e-7:
                errors.append(f"transition {tid} {level} landing/fallback blocked or unsupported; reserve {inset:g}m landing clearance")
            if not all(nav.on_floor(endpoint[0]-dz/run*side, endpoint[2]+dx/run*side) for side in [-transition["width"]/2,0,transition["width"]/2]):
                errors.append(f"transition {tid} {level} endpoint has a gap or unsupported edge across ramp width")
        # No obstacle or intermediate slab may enter the swept body corridor.
        for n in range(33):
            t = n/32
            x, y, z = [entry[i]+(exit[i]-entry[i])*t for i in range(3)]
            for obj in world["objects"]:
                asset = assets[obj["asset_id"]]
                if not asset["collision"]["enabled"]:
                    continue
                halfx = asset["footprint"][0]*asset["scale"][0]*obj["scale"][0]/2
                halfz = asset["footprint"][1]*asset["scale"][2]*obj["scale"][2]/2
                # Conservative rotated footprint bounding square.
                angle = math.radians(obj["rotation_y"]+asset["rotation_y"])
                sx = abs(math.cos(angle))*halfx+abs(math.sin(angle))*halfz+radius
                sz = abs(math.sin(angle))*halfx+abs(math.cos(angle))*halfz+radius
                bottom = obj["position"][1]+(asset["collision"]["offset"][1]-asset["collision"]["size"][1]/2)*obj["scale"][1]*asset["scale"][1]
                top = bottom+asset["collision"]["size"][1]*obj["scale"][1]*asset["scale"][1]
                if abs(x-obj["position"][0]) < sx and abs(z-obj["position"][2]) < sz and top > y+.05 and bottom < y+height:
                    errors.append(f"transition {tid} swept body/headroom blocked by {obj['id']}")
                    break
        transition_edges.append((source, dest, *landings))
    if errors:
        return list(dict.fromkeys(errors))
    spawn_levels = [level for level, elevation in levels.items() if abs(world["spawn"][1]-elevation) < 1e-7 and navigators[level].walkable(world["spawn"][0], world["spawn"][2])]
    if not spawn_levels:
        return ["spawn is blocked or unsupported on every level"]
    reached = {}
    seeds = [(spawn_levels[0], world["spawn"])]
    while seeds:
        level, point = seeds.pop()
        component = navigators[level].reachable(point)
        if component <= reached.get(level, set()):
            continue
        reached.setdefault(level, set()).update(component)
        for source, dest, first, last in transition_edges:
            for a, b, pa, pb in [(source, dest, first, last), (dest, source, last, first)]:
                if level == a and navigators[a].connects(pa, reached[a]) and not navigators[b].connects(pb, reached.get(b, set())):
                    seeds.append((b, pb))
    for station in world["stations"]:
        level = station.get("level_id")
        if level not in levels:
            errors.append(f"station {station['id']} references unknown level")
            continue
        for name in ["approach", "interaction"]:
            point = station[name]
            if abs(point[1]-levels[level]) > 1e-7 or not navigators[level].connects(point, reached.get(level, set())):
                errors.append(f"station {station['id']} {name} blocked, unsupported or unreachable on level {level}")
    cell = world["navigation"]["cell_size"]
    for zone in world["zones"]:
        if not any(abs(x*cell-zone["center"][0]) <= zone["size"][0]/2 and abs(z*cell-zone["center"][2]) <= zone["size"][1]/2
                   for x,z in reached.get(zone["level_id"], set())):
            errors.append(f"zone {zone['id']} has no reachable circulation from spawn; connect its floor or add a supported transition")
    return errors
