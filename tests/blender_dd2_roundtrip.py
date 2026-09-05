import sys
from pathlib import Path
import importlib
import json
import bpy
import addon_utils
import numpy as np
import argparse
import tempfile

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('assets',type=Path)
parser.add_argument('output',type=Path)
parser.add_argument('--pattern',default='*.mesh.260421070')
parser.add_argument('--edit',action='store_true')
parser.add_argument('--materials',action='store_true')
args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
args.assets = args.assets.resolve()
args.output = args.output.resolve()
sys.path.insert(0, str(root.parent))
addon = addon_utils.enable(root.name, default_set=True)
assert addon is not None
bpy.context.preferences.addons[root.name].preferences.showConsole = False
bpy.context.preferences.addons[root.name].preferences.textureCachePath = str(args.output / 'texture-cache')
mesh = importlib.import_module(root.name+'.modules.mesh.file_re_mesh')
parse = importlib.import_module(root.name+'.modules.mesh.re_mesh_parse')
output = args.output
output.mkdir(parents=True,exist_ok=True)
output = Path(tempfile.mkdtemp(prefix='dd2-roundtrip-',dir=output))
print('TEST_OUTPUT',output)
results = []
def compare(a, b, compare_weights=True):
    assert [bone.boneName for bone in a.skeleton.boneList] == [bone.boneName for bone in b.skeleton.boneList]
    assert [bone.parentIndex for bone in a.skeleton.boneList] == [bone.parentIndex for bone in b.skeleton.boneList]
    def items(parsed):
        return {(li,g.visconGroupNum,s.subMeshIndex):(parsed.materialNameList[s.materialIndex],s)
            for li,lod in enumerate(parsed.mainMeshLODList) for g in lod.visconGroupList for s in g.subMeshList}
    lhs, rhs = items(a), items(b)
    assert lhs.keys() == rhs.keys(), (lhs.keys(),rhs.keys())
    for key, (material,x) in lhs.items():
        material2,y = rhs[key]
        assert material == material2, (key,material,material2)
        for field in ('vertexPosList','faceList','uvList','uv2List'):
            np.testing.assert_allclose(getattr(x,field),getattr(y,field),atol=2e-5,rtol=0,err_msg=str(key)+' '+field)
        for indices,weights in ((('weightIndicesList','weightList'),('secondaryWeightIndicesList','secondaryWeightList')) if compare_weights else ()):
            def named_weights(parsed, sub):
                return [dict(sorted((parsed.skeleton.weightedBones[i],round(w,6)) for i,w in zip(ii,ww) if w)
                    ) for ii,ww in zip(getattr(sub,indices),getattr(sub,weights))]
            assert named_weights(a,x) == named_weights(b,y), (key,weights)
for path in sorted(args.assets.rglob(args.pattern)):
    if 'streaming' in path.parts:
        continue
    result = bpy.ops.re_mesh.importfile(directory=str(path.parent), files=[{'name':path.name}], clearScene=True, loadMaterials=args.materials,
        loadMDFData=args.materials, loadShellFur=False, importAllLODs=True)
    assert result == {'FINISHED'}, (path, result)
    collection = bpy.context.scene.re_mdf_toolpanel.meshCollection
    objects = [o for o in collection.all_objects if o.type == 'MESH']
    assert objects, path
    if args.materials:
        loaded_images = [i for i in bpy.data.images if i.source == 'FILE' and i.size[0] > 0 and i.has_data]
        print('MATERIAL_IMAGES',[(i.name,i.source,list(i.size),i.has_data) for i in bpy.data.images])
        assert loaded_images, 'No material textures loaded'
        assert bpy.context.scene.re_mdf_toolpanel.activeGame == 'DD2'
    if args.edit:
        vertex = objects[0].data.vertices[0]
        old_x = vertex.co.x
        vertex.co.x += 0.125
        assert abs(vertex.co.x-old_x-0.125)<1e-6
        objects[0].data.update()
    exported = output / Path(path.name).with_suffix('.260421070')
    result = bpy.ops.re_mesh.exportfile(filepath=str(exported), targetCollection=collection.name,
        exportAllLODs=True, preserveBoneMatrices=True)
    assert exported.is_file(), (path, result)
    original = parse.ParsedREMesh()
    original.ParseREMesh(mesh.readREMesh(str(path)))
    reread = mesh.readREMesh(str(exported))
    rebuilt = parse.ParsedREMesh()
    rebuilt.ParseREMesh(reread)
    assert reread.fileHeader.bufferCount == 1
    assert len(original.skeleton.boneList) == len(rebuilt.skeleton.boneList)
    legacy_path = exported.with_suffix('.240423143')
    bpy.ops.re_mesh.exportfile(filepath=str(legacy_path), targetCollection=collection.name,
        exportAllLODs=True, preserveBoneMatrices=True)
    assert legacy_path.is_file()
    legacy = parse.ParsedREMesh()
    legacy.ParseREMesh(mesh.readREMesh(str(legacy_path)))
    compare(legacy, rebuilt)
    if args.edit:
        old_positions = [s.vertexPosList for lod in original.mainMeshLODList for g in lod.visconGroupList for s in g.subMeshList]
        new_positions = [s.vertexPosList for lod in rebuilt.mainMeshLODList for g in lod.visconGroupList for s in g.subMeshList]
        assert old_positions != new_positions, 'Edited geometry was not exported'
    assert len(original.mainMeshLODList) == len(rebuilt.mainMeshLODList)
    results.append(dict(file=path.name, objects=len(objects), bytes=exported.stat().st_size))
    print('BLENDER_ROUNDTRIP_OK', path.name, flush=True)
assert results, 'No meshes tested'
(output / 'validation-blender-roundtrip.json').write_text(json.dumps(results,indent=2))
print('BLENDER_ROUNDTRIP_PASSED', len(results), flush=True)
