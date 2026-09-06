"""Actual MDF normal/batch export regression; open a saved blend in isolation."""
import argparse
import hashlib
import importlib
import json
from pathlib import Path
import sys

import addon_utils
import bpy

parser = argparse.ArgumentParser()
parser.add_argument('output', type=Path)
parser.add_argument('access_log', type=Path)
parser.add_argument('--addon-root', type=Path)
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
root = args.addon_root.resolve() if args.addon_root else Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root.parent))
addon = addon_utils.enable(root.name, default_set=True)
assert addon
assert Path(addon.__file__).resolve() == root/'__init__.py'
bpy.context.preferences.addons[root.name].preferences.showConsole = False
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=True)
source = Path(bpy.data.filepath)
source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
panel = bpy.context.scene.re_mdf_toolpanel
panel.activeGame = 'DD2'
panel.modDirectory = str(out)
collection = bpy.data.collections['tops_036_wb_f.mdf2']
collection.re_mdf_export_name = ''
legacy_name = 'tops_036_wb_f.mdf2.51'
game_name = 'tops_036_wb_f_00.mdf2.51'
normal = out / 'normal'
normal.mkdir(exist_ok=True)
status = bpy.ops.re_mdf.exportfile(filepath=str(normal/legacy_name), targetCollection=collection.name)
assert status == {'FINISHED'} and (normal/legacy_name).is_file()
baseline = (normal/legacy_name).read_bytes()
status = bpy.ops.re_mdf.check_dd2_export_name(filepath=str(args.access_log), targetCollection=collection.name)
assert status == {'FINISHED'}
assert collection.re_mdf_export_name == 'tops_036_wb_f_00.mdf2'
assert bpy.ops.re_mdf.exportfile(filepath=str(normal/legacy_name), targetCollection=collection.name) == {'FINISHED'}
assert (normal/game_name).read_bytes() == baseline
assert collection['BatchExport_path'] == str(normal/game_name)

# Missing and unrelated logs must neither erase the selected name nor gate export.
empty_log = out / 'unrelated.txt'
empty_log.write_text('unrelated\n')
for path in (empty_log, out/'missing.txt'):
    assert bpy.ops.re_mdf.check_dd2_export_name(filepath=str(path), targetCollection=collection.name) == {'FINISHED'}
    assert collection.re_mdf_export_name == 'tops_036_wb_f_00.mdf2'

# Selecting a variant is explicit; returning to the current choice changes no data.
choices = json.dumps(['tops_036_wb_f_00.mdf2', 'tops_036_wb_f_01.mdf2'])
assert bpy.ops.re_mdf.choose_dd2_export_name(targetCollection=collection.name, names_json=choices,
                                           choice='tops_036_wb_f_01.mdf2') == {'FINISHED'}
assert collection.re_mdf_export_name == 'tops_036_wb_f_01.mdf2'
assert bpy.ops.re_mdf.choose_dd2_export_name(targetCollection=collection.name, names_json=choices,
                                           choice='tops_036_wb_f_00.mdf2') == {'FINISHED'}

batch = out / 'batch'
batch.mkdir(exist_ok=True)
batch_item = {prop.identifier:prop.default for prop in addon.ExporterNodePropertyGroup.bl_rna.properties
              if prop.identifier != 'rna_type'}
batch_item.update(name=collection.name, path=str(batch/legacy_name), exportType='MDF',
                  enabled=True, invalid=False, hasChild=False)
assert bpy.ops.re_mesh.batch_exporter(itemList_items=[batch_item]) == {'FINISHED'}
assert (batch/game_name).read_bytes() == baseline
assert not (batch/legacy_name).exists()

# The path shown when populating the batch dialog must also use the chosen name.
operators = importlib.import_module(root.name+'.modules.mesh.re_mesh_operators')
collection['BatchExport_path'] = str(batch/legacy_name)
settings = bpy.context.scene.re_mdf_toolpanel
# Collection-list helper is exercised through its real PropertyGroup collection.
bpy.types.Scene.dd2_test_items = bpy.props.CollectionProperty(type=addon.ExporterNodePropertyGroup)
operators.populateCollectionList(bpy.context.scene.dd2_test_items, collection, 0, '')
assert bpy.context.scene.dd2_test_items[0].path == str(batch/game_name)
del bpy.types.Scene.dd2_test_items

panel.activeGame = 'RE9'
other = out / 'other-game'
other.mkdir(exist_ok=True)
assert bpy.ops.re_mdf.exportfile(filepath=str(other/legacy_name), targetCollection=collection.name) == {'FINISHED'}
assert (other/legacy_name).is_file() and not (other/game_name).exists()
panel.activeGame = 'DD2'
collection.re_mdf_export_name = ''
cleared = out / 'cleared'
cleared.mkdir(exist_ok=True)
assert bpy.ops.re_mdf.exportfile(filepath=str(cleared/legacy_name), targetCollection=collection.name) == {'FINISHED'}
assert (cleared/legacy_name).is_file() and not (cleared/game_name).exists()

# The per-collection choice must survive saving/loading a Blender library.
collection.re_mdf_export_name = 'tops_036_wb_f_00.mdf2'
library_path = out/'name-persistence.blend'
bpy.data.libraries.write(str(library_path), {collection})
with bpy.data.libraries.load(str(library_path)) as (available, loaded):
    loaded.collections = [collection.name]
assert loaded.collections[0].re_mdf_export_name == 'tops_036_wb_f_00.mdf2'

assert hashlib.sha256(source.read_bytes()).hexdigest() == source_hash
addon_utils.disable(root.name, default_set=True, refresh_handled=True)
assert not hasattr(bpy.types.Collection, 're_mdf_export_name')
assert addon_utils.enable(root.name, default_set=True)
assert hasattr(bpy.types.Collection, 're_mdf_export_name')
result = {'source':str(source),'source_unchanged':True,'mdf_bytes':len(baseline),
    'mdf_sha256':hashlib.sha256(baseline).hexdigest(), 'normal_batch_equal':True,
    'unknown_log_keeps_choice':True,'explicit_variant_choice':True,'clear_and_other_game_preserved':True,
    'registration_cycle':True,'blend_name_persistence':True}
(out/'results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('DD2_MDF_EXPORT_NAME_PASS',json.dumps(result),flush=True)
