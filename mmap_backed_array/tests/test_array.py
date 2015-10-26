import sys
import py

class BaseArrayTests:
    def test_ctor(self):
        assert len(self.array('c')) == 0
        assert len(self.array('i')) == 0

        raises(TypeError, self.array, 'hi')
        raises(TypeError, self.array, 1)
        raises(ValueError, self.array, 'q')



class TestArray(BaseArrayTests):
    def setup_class(cls):
        import mmap_backed_array
        cls.array = mmap_backed_array.mmaparray
        import struct
        cls.struct = struct
        cls.tempfile = str(py.test.ensuretemp('mmaparray').join('tmpfile'))
        cls.maxint = sys.maxsize #get the biggest addressable size
