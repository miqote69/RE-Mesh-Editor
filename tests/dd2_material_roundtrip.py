import importlib,sys,types,json
import argparse
import tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('assets',type=Path)
parser.add_argument('output',type=Path)
args=parser.parse_args()
p=types.ModuleType('mesh_probe');p.__path__=[str(root)];sys.modules['mesh_probe']=p
mdf=importlib.import_module('mesh_probe.modules.mdf.file_re_mdf')
tex=importlib.import_module('mesh_probe.modules.tex.file_re_tex')
texutils=importlib.import_module('mesh_probe.modules.tex.re_tex_utils')
out=args.output;out.mkdir(parents=True,exist_ok=True)
out=Path(tempfile.mkdtemp(prefix='dd2-materials-',dir=out))
print('TEST_OUTPUT',out)
def signature(m):
    return [(s.materialName,[(t.textureType,t.texturePath) for t in s.textureList],
             [(p.propName,p.propValue) for p in s.propertyList]) for s in m.materialList]
results=[]
for path in args.assets.rglob('*.mdf2.51'):
    original=mdf.readMDF(str(path))
    target=out/path.name
    mdf.writeMDF(original,str(target))
    after=mdf.readMDF(str(target))
    assert signature(original)==signature(after)
    results.append({'file':path.name,'materials':len(original.materialList)})
textures=[]
for path in sorted(args.assets.rglob('*.tex.251211553')):
    original=tex.RE_TexFile();original.read(str(path))
    target=out/path.name
    dds_info=texutils.convertTexFileToDDS(str(path),str(out/(path.name+'.dds')))
    texutils.DDSToTex(dds_info['outDDSList'],251211553,str(target))
    after=tex.RE_TexFile();after.read(str(target))
    for field in ('version','width','height','depth','imageCount','mipCount','format','cubemapMarker'):
        assert getattr(original.tex.header,field)==getattr(after.tex.header,field),field
    for i in range(original.tex.header.imageCount):
        assert original.tex.GetTextureData(i)==after.tex.GetTextureData(i)
    textures.append(path.name)
assert textures, 'No current textures tested'
assert results, 'No current materials tested'
(out/'validation-materials.json').write_text(json.dumps({'mdf':results,'textures':textures},indent=2))
print('MATERIALS_TEXTURES_PASS',len(results),len(textures))
