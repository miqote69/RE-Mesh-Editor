import json
import os

import bpy
from bpy_extras.io_utils import ImportHelper

from .mdf_export_name import mdf_log_candidates, resolve_export_name


def collection_export_path(filepath, collection, context):
    if collection is None:
        return filepath
    return resolve_export_name(filepath, context.scene.re_mdf_toolpanel.activeGame,
                               collection.re_mdf_export_name)


def update_game_mdf_name(collection, context):
    # Keep Blender's visible filename (and overwrite prompt) in sync with the
    # choice made by the log-check button or the editable Name field.
    if context is None:
        return
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type != 'FILE_BROWSER':
                continue
            space = area.spaces.active
            operator = space.active_operator
            if (operator is None or operator.bl_rna.identifier != 'RE_MDF_OT_exportfile'
                    or operator.targetCollection != collection.name or space.params is None):
                continue
            try:
                space.params.filename = collection_export_path(space.params.filename, collection, context)
            except ValueError:
                pass  # Allow editing an incomplete name; execute reports it before writing.
            area.tag_redraw()


def find_dd2_log(context):
    paths = set()
    for library in context.preferences.filepaths.asset_libraries:
        info = os.path.join(bpy.path.abspath(library.path), 'ExtractInfo_DD2.json')
        try:
            with open(info, encoding='utf-8-sig') as stream:
                exe = json.load(stream).get('exePath', '')
            log = os.path.join(os.path.dirname(exe), 'reframework_accessed_files.txt')
            if exe and os.path.isfile(log):
                paths.add(log)
        except (OSError, ValueError, TypeError):
            continue
    return next(iter(paths)) if len(paths) == 1 else ''


class WM_OT_CheckDD2MDFName(bpy.types.Operator, ImportHelper):
    """Read the equipped costume's MDF names from a DD2 accessed-files log"""
    bl_idname = 're_mdf.check_dd2_export_name'
    bl_label = 'Check DD2 game log'
    bl_options = {'UNDO'}

    filename_ext = '.txt'
    filter_glob: bpy.props.StringProperty(default='*.txt', options={'HIDDEN'})
    targetCollection: bpy.props.StringProperty(options={'HIDDEN'})
    mdfVersion: bpy.props.IntProperty(default=51, options={'HIDDEN'})

    def invoke(self, context, event):
        if not self.filepath:
            self.filepath = find_dd2_log(context)
        if self.filepath:
            return self.execute(context)
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        collection = bpy.data.collections.get(self.targetCollection)
        if collection is None or context.scene.re_mdf_toolpanel.activeGame != 'DD2':
            self.report({'WARNING'}, 'Select a DD2 MDF collection first.')
            return {'CANCELLED'}
        try:
            with open(self.filepath, encoding='utf-8-sig', errors='replace') as stream:
                names = mdf_log_candidates(stream, collection.get('~ASSETPATH', ''), self.mdfVersion)
        except OSError as error:
            self.report({'WARNING'}, f'Could not read game log: {error}. Export name unchanged.')
            return {'FINISHED'}
        if len(names) == 1:
            collection.re_mdf_export_name = names[0]
            self.report({'INFO'}, f'Game MDF name: {names[0]} (from this log).')
        elif names:
            bpy.ops.re_mdf.choose_dd2_export_name('INVOKE_DEFAULT',
                targetCollection=collection.name, names_json=json.dumps(names))
        else:
            self.report({'WARNING'}, 'No matching MDF references in this log. Export name unchanged.')
        return {'FINISHED'}


class WM_OT_ChooseDD2MDFName(bpy.types.Operator):
    """Choose the costume variant to receive this MDF"""
    bl_idname = 're_mdf.choose_dd2_export_name'
    bl_label = 'Choose game MDF name'
    bl_options = {'UNDO'}

    targetCollection: bpy.props.StringProperty(options={'HIDDEN'})
    names_json: bpy.props.StringProperty(default='[]', options={'HIDDEN'})
    _items = []

    def name_items(self, context):
        # Keep strings alive for Blender's dynamic EnumProperty.
        items = [(name, name, '') for name in json.loads(self.names_json)]
        if items != WM_OT_ChooseDD2MDFName._items:
            WM_OT_ChooseDD2MDFName._items = items
        return WM_OT_ChooseDD2MDFName._items

    choice: bpy.props.EnumProperty(name='Costume MDF', items=name_items)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=520)

    def draw(self, context):
        self.layout.label(text='Multiple MDF names were accessed. Select the intended costume.')
        self.layout.prop(self, 'choice')

    def execute(self, context):
        collection = bpy.data.collections.get(self.targetCollection)
        if collection is None or self.choice not in json.loads(self.names_json):
            return {'CANCELLED'}
        collection.re_mdf_export_name = self.choice
        self.report({'INFO'}, f'Game MDF name: {self.choice}')
        return {'FINISHED'}


def draw_dd2_export_name(layout, context, collection, version=51):
    if context.scene.re_mdf_toolpanel.activeGame != 'DD2' or collection is None:
        return
    box = layout.box()
    box.label(text='DD2 game MDF filename')
    box.prop(collection, 're_mdf_export_name', text='Name')
    op = box.operator('re_mdf.check_dd2_export_name', icon='VIEWZOOM')
    op.targetCollection = collection.name
    op.mdfVersion = version
    if not collection.re_mdf_export_name:
        box.label(text='Game filename not checked. Export uses the entered filename.', icon='INFO')
    box.label(text='Clear Name to use the entered filename.')
