# DD2 September 2026 patch validation

Required path: current DD2 asset -> Blender 5.2 import -> edited mesh export
as `.mesh.260421070`, preserving geometry, UVs, skeleton and DD2 secondary weights.
Old `.mesh.240423143` import/export must continue to work. Texture/material
version selection must match the current game. Unknowns must not be presented
as tested support.

Regression cases: old/new file header round-trip, current-game armor import,
unmodified import/export/reimport comparison of positions, faces, bones and
weights, an edited mesh export, and truncated input. Real game files stay local;
no extracted game assets are committed. Blender tests use a factory-startup
process and isolated output, without changing installed addons or game files.

Game rendering and character deformation are distinct from Blender/file tests.
Record results here after execution; no in-game acceptance is claimed yet.

## Evidence, September 6, 2026

Target: DD2 Title Update 3.2, local Steam build `24831693`; Blender 5.2.0 LTS
`fbe6228777e7`. The [official Steam announcement](https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1842846814439031)
announces TU3.2. Format research used kagenocookie's
[RE-Engine-Lib DD2 changes](https://github.com/kagenocookie/RE-Engine-Lib/commit/d149dce3a59178fbcbb274bbf3cd9ac5df6cfdbe),
checked against bytes extracted from the installed game.

| Data | Before | Current |
|---|---|---|
| MESH filename version | 240423143 | 260421070 |
| MESH internal version | 230517984 | 251205828 |
| MDF2 version | 40 | 51 |
| TEX version | 760230703 | 251211553 |

- PASS: 29 current armor/body meshes imported into Blender and exported to both
  current and previous DD2 formats. Parsed outputs agree on LOD/group/submesh
  structure, material references, vertex positions, faces, UVs, bone names and
  parent indices, and named primary/secondary weights.
- PASS: a current mantle imported with MDF data and eight decoded texture
  images. A vertex was moved by 0.125 Blender units, exported and reread;
  the edit is present and both output formats agree.
- PASS: an existing user-created `.mesh.240423143` armor imported and exported
  in both formats. Source Mod files were read only and remain local.
- PASS: 33 current MDF files preserve material names, texture bindings and
  property values on file round-trip. 34 current TEX files, including arrays,
  preserve image data and dimensions through the actual TEX -> DDS -> TEX path.
- Unit regressions cover new/old headers, signed buffer offsets, secondary
  weight size/index fields and truncated new headers.

### Limits

In-game loading, rendering, physics and character-slider deformation are
**UNEXECUTED**. Streaming meshes with multiple vertex buffers, face morph
export and shell fur were not validated by this sample; upstream limitations
remain. This release must not be described as complete game compatibility.

The exporter retains upstream weight normalization/quantization and Blender
mesh validation. For example, `mantle_017_f` has one fewer triangle after
Blender import/export, and `mantle_012_f` weights change during normalization. Therefore
the Blender round-trip check compares new-format export with the established
legacy export of the same scene; it does **not** claim byte-exact preservation
of the untouched game file. No new weight cleanup policy was added.

## Reproducing the checks

Run in an isolated output directory, with legally obtained local game assets.
No game assets are included. Python checks need the Blender-bundled numpy.

```text
python -B -m unittest discover -s tests -p "test_*.py"
blender --background --factory-startup --python-exit-code 1 --python tests/blender_dd2_roundtrip.py -- ASSET_DIRECTORY OUTPUT_DIRECTORY
blender --background --factory-startup --python-exit-code 1 --python tests/blender_dd2_roundtrip.py -- ASSET_DIRECTORY EDIT_OUTPUT --pattern mantle_012_f.mesh.260421070 --edit --materials
python -B tests/dd2_material_roundtrip.py ASSET_DIRECTORY MATERIAL_OUTPUT
```

Keep `BLENDER_USER_CONFIG` and `BLENDER_USER_SCRIPTS` pointed at temporary
test directories when running addon registration tests. The scripts do not
install the fork into Blender or write into the game directory.
