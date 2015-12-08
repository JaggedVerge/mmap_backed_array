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

class Test_anon_mmap:
    """Test anonymous mmap helper"""

    def test_shm_open(self, monkeypatch):
        from mmap_backed_array import C, anon_mmap
        def shm_open(name, oflag, mode):
            assert isinstance(name, bytes)
            fwd_slash = ord(b'/')
            assert name[0] == fwd_slash
            assert fwd_slash not in name[1:]
            assert len(name) <= 255
            assert oflag == os.O_RDWR|os.O_CREAT|os.O_EXCL
            assert mode == 0o600
            return -1
        monkeypatch.setattr(C, 'shm_open', shm_open)
        pytest.raises(OSError, anon_mmap, b'\x00')

    def test_mmap(self, monkeypatch):
        import mmap_backed_array
        marker = object()
        data = b'Sample data!'
        def mmap(fd, size, *args, **kwargs):
            assert fd >= 0
            assert size == len(data)
            assert not args
            assert not kwargs
            return marker
        monkeypatch.setattr(mmap_backed_array._mmap, 'mmap', mmap)
        assert mmap_backed_array.anon_mmap(data) is marker

    def test_shm_unlink(self, monkeypatch):
        from mmap_backed_array import C, anon_mmap
        _unlink = C.shm_unlink
        def shm_unlink(name):
            assert _unlink(name) >= 0
            return -1
        monkeypatch.setattr(C, 'shm_unlink', shm_unlink)
        pytest.raises(OSError, anon_mmap, b'\x00')


class Test_mmaparray:

    def setup_class(cls):
        from mmap_backed_array import mmaparray, _mmap
        cls.mmaparray = mmaparray
        cls._mmap = _mmap
        cls.tempfile = str(pytest.ensuretemp('mmaparray').join('tmpfile'))

    def test_too_many_args(self):
        pytest.raises(TypeError, self.mmaparray, 'b', (), ())

    def test_unknown_kwargs(self):
        pytest.raises(TypeError, self.mmaparray, 'b', (), foo=1)

    def test_mmap_typeerror(self):
        pytest.raises(TypeError, self.mmaparray, 'b', mmap=object())
