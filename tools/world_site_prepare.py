"""Prepare a private Sites adapter from validated runtime revisions and a Web export.

Operator boundary: runtime source and exported PCK are reviewed code. Data is
validated again here, never accepted on the strength of a claimed receipt.
"""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
from pathlib import Path
try:
    from .validate_content import ContentValidator
    from .world_author import DEFAULT_POLICY, bundle, check_root, content_hash, enforce_policy, is_link, operation_diff, tree_files
    from .world_revision_guards import enforce_revision_guards
except ImportError:
    from validate_content import ContentValidator
    from world_author import DEFAULT_POLICY, bundle, check_root, content_hash, enforce_policy, is_link, operation_diff, tree_files
    from world_revision_guards import enforce_revision_guards


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode()


def _no_links(path: Path) -> None:
    """Reject reparse points before resolve can erase evidence of a link."""
    current = path.absolute()
    while True:
        if is_link(current):
            raise ValueError('Links and junctions forbidden: '+str(current))
        if current.parent == current:
            break
        current = current.parent


def _safe_public_tree(site: Path) -> None:
    public=site/'public'
    _no_links(public)
    if public.exists():
        for path in public.rglob('*'):
            if is_link(path):
                raise ValueError('Site public links and junctions forbidden: '+str(path))


def prepare(site: Path, web: Path, roots: list[Path], world_id: str) -> dict:
    _no_links(site)
    _no_links(web)
    site, web = site.resolve(), web.resolve()
    for path in [site/'.openai/hosting.json',site/'lib/world/registry.json',site/'world-deployment-receipt.json']:
        _no_links(path)
    _safe_public_tree(site)
    if not (site/'.openai/hosting.json').is_file():
        raise ValueError('Prepare an isolated Sites starter before packaging')
    if not 1 <= len(roots) <= 10:
        raise ValueError('Require 1..10 validated revisions')
    # Validate the complete trusted export and exact supported loader BEFORE
    # any output. A malformed candidate/export leaves the previous Site bytes.
    required={'index.html','index.js','index.wasm','index.pck'}
    for name in required:
        _no_links(web/name)
    if not all((web/name).is_file() for name in required):
        raise ValueError('Incomplete reviewed Godot Web export')
    exported={}
    for path in web.iterdir():
        if path.is_file() and path.suffix in {'.html','.js','.png','.svg','.pck'}:
            _no_links(path)
            _no_links(site/'public/world'/path.name)
            exported[path.name]=path.read_bytes()
    engine=(web/'index.wasm').read_bytes()
    compressed_engine=gzip.compress(engine,compresslevel=9,mtime=0)
    script=exported['index.js'].decode('utf-8').replace('\r\n','\n')
    needle='loadPromise = preloader.loadPromise(`${loadPath}.wasm`, size, true);'
    if script.count(needle)!=1:
        raise ValueError('Unsupported Godot loader; review before patching')
    script=script.replace(needle,"loadPromise = fetch(`${loadPath}.wasm.gz`, {credentials:'same-origin'}).then(response => { if (!response.ok) throw new Error('Engine download failed'); return response.arrayBuffer().then(bytes => { const v=new Uint8Array(bytes); const stream=(v[0]===31 && v[1]===139) ? new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip')) : new Blob([bytes]).stream(); return new Response(stream,{headers:{'content-type':'application/wasm'}}); }); });")
    html=exported['index.html'].decode('utf-8').replace('\r\n','\n')
    if html.count('engine.startGame({') != 1 or html.count('}).then(() => {\n\t\t\tsetStatusMode') != 1:
        raise ValueError('Unsupported Godot startup HTML; review before patching')
    if html.count('<script src="index.js"></script>') != 1:
        raise ValueError('Missing HTML loader insertion anchor')
    html=html.replace('<script src="index.js"></script>', '<script src="/world-host.js"></script>\n<script src="index.js"></script>')
    html=html.replace('engine.startGame({','window.domesHostReady.then(() => engine.startGame({').replace('}).then(() => {\n\t\t\tsetStatusMode','})).then(() => {\n\t\t\tsetStatusMode')
    exported.update({'index.js':script.encode('utf-8'),'index.html':html.encode('utf-8'),'index.wasm.gz':compressed_engine})
    records, base = {}, None
    validated_sources=[]
    data_dir=site/'public/world-data'
    pending_data={}
    for number, root in enumerate(roots, 1):
        _no_links(root)
        root=root.resolve()
        check_root(root)
        tree_files(root/'schemas')
        source_hash=content_hash(root/'godot/content')
        validator=ContentValidator(root)
        errors=validator.validate()
        if errors:
            raise ValueError('Revision failed validation: '+'; '.join(errors))
        full=bundle(validator,world_id)
        if base is None:
            base=full
        elif full['character'] != base['character'] or full['routine'] != base['routine'] or full['world']['version'] != base['world']['version']:
            raise ValueError('Dynamic revision requires identical character, routine and compatible world version')
        enforce_revision_guards(base, full)
        if full['brief']['owner_locked'] != base['brief']['owner_locked']:
            raise ValueError('Revision cannot change owner locks')
        operations=operation_diff(base,full)
        policy=base['brief']['owner_locked'].get('authoring_policy',DEFAULT_POLICY)
        policy_errors=validator.validate_document('owner-policy',policy)
        if policy_errors:
            raise ValueError('Invalid owner policy: '+'; '.join(policy_errors))
        policy_errors,_=enforce_policy(policy,base,full,operations,validator)
        if policy_errors:
            raise ValueError('Revision violates owner policy: '+'; '.join(policy_errors))
        if operations and policy['autonomy']!='within_bounds':
            raise ValueError('Owner policy is proposal_only; no JSON approval override')
        if operations & {'add_zone','add_level','add_transition','modify_zone','modify_level','modify_transition'}:
            migration=full['world']['metadata'].get('revision_state',{}).get('state_migration')
            expected={'strategy':'preserve_existing_ids_and_routine','routine_id':base['routine']['id'],'reset_transient_navigation':True}
            if migration!=expected:
                raise ValueError('Structural revision requires explicit identity-preserving state migration')
        for kind in ('objects','stations','zones'):
            if not {v['id'] for v in base['world'][kind]} <= {v['id'] for v in full['world'][kind]}:
                raise ValueError('Identity-preserving migration cannot remove '+kind)
        if len(full['assets'])>128 or len(full['world']['objects'])>256:
            raise ValueError('Dynamic data geometry budget exceeded')
        for asset in full['assets'].values():
            if asset['scene_path'] or len(asset['parts'])>64:
                raise ValueError('Dynamic assets must be bounded primitive recipes')
        data={key:full[key] for key in ('world','character','routine','assets')}
        raw=encoded(data)
        if len(raw)>2097152:
            raise ValueError('Dynamic bundle exceeds 2MiB intake bound')
        sha=hashlib.sha256(raw).hexdigest()
        destination=data_dir/(sha+'.json')
        _no_links(destination)
        if destination.exists() and destination.read_bytes()!=raw:
            raise ValueError('Existing immutable bundle has conflicting bytes')
        pending_data[sha+'.json']=raw
        records[str(number)]={'bundle_url':'/world-data/'+sha+'.json','sha256':sha,
            'world_version':full['world']['version'],'character_id':full['character']['id'],
            'routine_id':full['routine']['id'],'project_ids':[p['id'] for p in full['routine']['projects']],
            'title':full['world']['title'],'migration':'preserve_existing_ids_and_routine',
            'source_hash':source_hash}
        validated_sources.append((root,source_hash))
    registry={'world_id':world_id,'default_revision':1,'revisions':records}
    # Only after every candidate/export check passes, update local packaging.
    # Content-addressed old bundles are deliberately retained for known-good
    # rollback; this adapter performs no cleanup or hosted activation.
    for root,source_hash in validated_sources:
        if content_hash(root/'godot/content')!=source_hash:
            raise ValueError('Source content changed during Site preparation; revalidate the current revision')
    _safe_public_tree(site)
    data_dir.mkdir(parents=True, exist_ok=True)
    for name,raw in pending_data.items():
        (data_dir/name).write_bytes(raw)
    (site/'lib/world').mkdir(parents=True,exist_ok=True)
    (site/'lib/world/registry.json').write_bytes(encoded(registry))
    target=site/'public/world'
    target.mkdir(parents=True,exist_ok=True)
    for name,raw in exported.items():
        (target/name).write_bytes(raw)
    receipt={'world_id':world_id,'revisions':records,'engine_uncompressed_bytes':len(engine),
        'engine_gzip_bytes':(target/'index.wasm.gz').stat().st_size,'engine_sha256':hashlib.sha256(engine).hexdigest(),
        'pck_sha256':hashlib.sha256((target/'index.pck').read_bytes()).hexdigest(),
        'data_lane':'validated primitive worlds; identical bundled character and routine',
        'files':{p.relative_to(site/'public').as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((site/'public').rglob('*')) if p.is_file()}}
    (site/'world-deployment-receipt.json').write_bytes(encoded(receipt))
    return receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--site',type=Path,required=True)
    parser.add_argument('--web',type=Path,required=True)
    parser.add_argument('--revision',type=Path,action='append',required=True)
    parser.add_argument('--world-id',required=True)
    args=parser.parse_args()
    receipt=prepare(args.site,args.web,args.revision,args.world_id)
    print(json.dumps({k:v for k,v in receipt.items() if k not in {'files','revisions'}},indent=2))
if __name__=='__main__':
    main()
