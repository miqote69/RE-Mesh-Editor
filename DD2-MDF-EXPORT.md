# DD2 MDF export names (0.66.2)

DD2 can request a numbered costume MDF while the imported collection uses
the mesh's unnumbered name. For example, a working in-game comparison used
`tops_036_wb_f_00.mdf2.51`, while the collection suggested
`tops_036_wb_f.mdf2.51`. Correct material contents under the wrong filename
do not replace the material the game requests.

## Usage

1. Select the DD2 MDF collection in **RE MDF Tools**.
2. Click **Check DD2 game log**. The tool reads
   `reframework_accessed_files.txt` from the configured DD2 asset library's
   game directory, or opens a file picker if it cannot determine one path.
3. If the log contains multiple matching costume names, choose the intended
   one. Inspect **Name**, then save the `.blend` to retain the choice.
4. Export normally or with RE Batch Exporter. The chosen name is applied to
   both paths, preserving the output directory and selected format version.

You can also enter a basename such as `tops_036_wb_f_00.mdf2` directly.
Do not include a directory or version number in **Name**. Clear it to return
to the manually entered export filename. The selected name also appears in
the MDF export dialog. Other games retain their existing naming behavior.

A log only describes resources accessed in that run. Equip the intended
costume before relying on its references. A missing or unrelated log leaves
the stored choice unchanged and does not prevent ordinary export. This
feature does not infer every costume variant or convert material contents.

## Verification

- Six filename regression tests plus four existing mesh-header tests passed.
- Blender 5.2 tests using the installed addon and a locally authored armor
  passed normal and batch export, explicit variant selection, missing and
  unrelated logs, clearing the name, other-game behavior, save/load
  persistence, and addon registration cycles.
- Normal and batch MDF outputs were byte-identical to the MDF that the user
  had confirmed rendered correctly in DD2. No game assets are included here.
- A second existing project exported eleven submeshes and eight matching MDF
  materials as MESH `260421070` and MDF `51`. Its saved project retained
  geometry, UVs, weights, bones, MDF data and the referenced image paths.

The export dialog's visual behavior and the second project's in-game display
remain unverified. These checks do not establish universal DD2 compatibility.

Run unit tests with `python -B -m unittest discover -s tests -p "test_*.py"`.
The Blender regression script is `tests/blender_dd2_export_name.py`; it takes
an output directory and an accessed-files log after `--`, with optional
`--addon-root`. Open a locally owned `.blend` containing the example armor's
MDF collection when running it. Set `BLENDER_USER_RESOURCES`,
`BLENDER_USER_CONFIG`, `BLENDER_USER_SCRIPTS`, and `BLENDER_USER_EXTENSIONS`
to isolated test directories. Do not use normal Blender preferences for
addon registration tests.
