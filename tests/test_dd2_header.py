import importlib
import io
from pathlib import Path
import struct
import sys
import types
import unittest

ROOT = Path(__file__).resolve().parents[1]
package = types.ModuleType('mesh_tests')
package.__path__ = [str(ROOT)]
sys.modules['mesh_tests'] = package
mesh = importlib.import_module('mesh_tests.modules.mesh.file_re_mesh')

class DD2HeaderTests(unittest.TestCase):
    def test_current_header_layout(self):
        header = mesh.FileHeader()
        header.version = 251205828
        header.bufferCount = 1
        header.meshGroupOffset = 176
        stream = io.BytesIO()
        version = mesh.meshFileVersionToNewVersionDict[260421070]
        header.write(stream, version)
        self.assertEqual(len(stream.getvalue()), 176)
        self.assertEqual(struct.unpack_from('<H', stream.getvalue(), 26)[0], 1)
        stream.seek(0)
        loaded = mesh.FileHeader()
        loaded.read(stream, version)
        self.assertEqual(loaded.bufferCount, 1)
        self.assertEqual(loaded.meshGroupOffset, 176)

    def test_previous_dd2_header(self):
        header = mesh.FileHeader()
        header.version = 230517984
        header.meshGroupOffset = 176
        version = mesh.meshFileVersionToNewVersionDict[240423143]
        stream = io.BytesIO()
        header.write(stream, version)
        self.assertEqual(len(stream.getvalue()), 176)
        stream.seek(0)
        loaded = mesh.FileHeader()
        loaded.read(stream, version)
        self.assertEqual(loaded.meshGroupOffset, 176)
        self.assertEqual(loaded.version, 230517984)

    def test_new_buffer_field_offsets(self):
        header = mesh.MeshBufferHeader()
        header.blendShapeOffsets = [-4096,-2048,-1024]
        header.secondaryWeightBufferSize = 256
        header.bufferIndex = 2
        stream = io.BytesIO()
        header.write(stream,mesh.VERSION_DD2_2026)
        self.assertEqual(struct.unpack_from('<3iII',stream.getvalue(),60),
                         (-4096,-2048,-1024,256,2))
        stream.seek(0)
        loaded = mesh.MeshBufferHeader()
        loaded.read(stream,mesh.VERSION_DD2_2026)
        self.assertEqual(loaded.blendShapeOffsets,header.blendShapeOffsets)
        self.assertEqual(loaded.secondaryWeightBufferSize,256)
        self.assertEqual(loaded.bufferIndex,2)

    def test_truncated_new_header_is_not_accepted(self):
        with self.assertRaises(struct.error):
            mesh.FileHeader().read(io.BytesIO(b'MESH'+bytes(20)),mesh.VERSION_DD2_2026)

if __name__ == '__main__':
    unittest.main()
