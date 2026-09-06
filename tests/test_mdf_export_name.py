import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('mdf_names', Path(__file__).resolve().parents[1] / 'modules/mdf/mdf_export_name.py')
names = importlib.util.module_from_spec(spec)
spec.loader.exec_module(names)
ASSET = 'character/_kit/_equipment/tops/036/tops_036_wb_f.mdf2'

def log(name, directory='character/_kit/_equipment/tops/036', version=51):
    return f'[2026-09-06 09:45:42.835] [LooseFileLoader] [info] D:/DD2/natives/STM/{directory}/{name}.mdf2.{version}\n'

class MDFNameTests(unittest.TestCase):
    def test_runtime_name_and_case_dedup(self):
        line = log('tops_036_wb_f_00')
        self.assertEqual(names.mdf_log_candidates([line, line.upper()], ASSET, 51), ['tops_036_wb_f_00.mdf2'])

    def test_other_armor_directories_versions_and_suffixes_excluded(self):
        lines = [log('tops_036_am_f_00'), log('tops_036_wb_f_00', directory='another/folder'),
                 log('tops_036_wb_f_00', version=40), log('tops_036_wb_f_extra'),
                 log('tops_036_wb_f_00') + 'extra', log('tops_036_wb_f_00').rstrip()+'.Ja']
        self.assertEqual(names.mdf_log_candidates(lines, ASSET, 51), [])

    def test_multiple_names_are_not_reduced_to_one(self):
        self.assertEqual(names.mdf_log_candidates([log('tops_036_wb_f_01'), log('tops_036_wb_f_00')], ASSET, 51),
                         ['tops_036_wb_f_00.mdf2', 'tops_036_wb_f_01.mdf2'])

    def test_preserves_directory_and_format(self):
        for version in (40, 51):
            path = rf'D:\Mod\tops_036_wb_f.mdf2.{version}'
            self.assertEqual(names.resolve_export_name(path, 'DD2', 'tops_036_wb_f_00.mdf2'),
                             rf'D:\Mod\tops_036_wb_f_00.mdf2.{version}')

    def test_no_choice_or_other_game_keeps_requested_path(self):
        path = '/mods/original.mdf2.51'
        self.assertEqual(names.resolve_export_name(path, 'DD2', ''), path)
        self.assertEqual(names.resolve_export_name(path, 'RE9', 'chosen.mdf2'), path)
        self.assertEqual(names.mdf_log_candidates([], ASSET, 51), [])

    def test_name_cannot_move_export_into_another_folder(self):
        for name in ('../elsewhere.mdf2', r'..\elsewhere.mdf2', 'D:elsewhere.mdf2', 'file.mdf2.51'):
            with self.assertRaises(ValueError):
                names.resolve_export_name('/mods/original.mdf2.51', 'DD2', name)

if __name__ == '__main__':
    unittest.main()
