import mmap_backed_array
import mmap
import os
import pytest

class TestMmap:
    """Test mmap implementation"""
    @classmethod
    def setup_class(cls):
        """set up temporary file to use as backing file"""
        cls.temp_file = str(pytest.ensuretemp('tempfiles').join('table.dat'))


    def test_create_file(self):
        with open(self.temp_file, 'wb+') as fd:
            fd.write(b'\x00')
            fd.flush()
            mmap_backing = mmap_backed_array._mmap.mmap(fd.fileno(), 1)
            arr = mmap_backed_array.mmaparray('I', mmap=mmap_backing)
            arr.append(1)
            arr.append(2)
            arr.append(3)
        mmap_backing.close()

    def test_read_only_mmap_backing(self):
        assert os.path.exists(os.path.dirname(self.temp_file))
        with open(self.temp_file, 'rb') as fd:
            mmap_backing = mmap.mmap(
                    fd.fileno(), 0, access=mmap.ACCESS_READ
                )
            arr = mmap_backed_array.mmaparray('I', mmap=mmap_backing)

            assert arr[0] == 1
        mmap_backing.close()
