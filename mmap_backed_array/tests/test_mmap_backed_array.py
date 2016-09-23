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

    def test_mmap_bad_typecode(self):
        """If created from an array.array the typecodes must match"""
        import array
        floats_array = array.array('f', (1.0, 2.0))
        with pytest.raises(TypeError):
            self.mmaparray('c', floats_array)

    def test_mmap_typecodes(self):
        import mmap_backed_array
        assert 'c' in mmap_backed_array.typecodes
        assert 'b' in mmap_backed_array.typecodes
        assert 'u' in mmap_backed_array.typecodes
        assert 'i' in mmap_backed_array.typecodes
        assert 'f' in mmap_backed_array.typecodes
        assert 'd' in mmap_backed_array.typecodes

    def test_mmaparray_from_array(self):
        """Test mmaparray can be created from an array.array"""
        import array
        int_array = array.array('i', (-1, 0, 1))
        test_mmap_array = self.mmaparray('i', int_array)
        assert test_mmap_array[0] == -1
        assert test_mmap_array[1] == 0
        assert test_mmap_array[2] == 1

    def test_mmaparray_setitem(self):
        """Test __setitem__ works as advertised"""
        import array
        int_array = array.array('i', (-1, 0, 1))
        test_mmap_array = self.mmaparray('i', int_array)
        assert test_mmap_array[0] == -1
        assert test_mmap_array[1] == 0
        assert test_mmap_array[2] == 1

        test_mmap_array[0] = 100
        assert test_mmap_array[0] == 100

        test_mmap_array[-1] = 3333
        assert test_mmap_array[-1] == 3333

        # Can't get index past end of the array
        with pytest.raises(IndexError):
            test_mmap_array[3] = 0

        # Can't get index that is past the beginning of the array
        with pytest.raises(IndexError):
            test_mmap_array[-4] = 0

    def test_extend_with_array(self):
        """Test mmaparray can be extended with array.array"""
        import array
        int_array = array.array('i', (0, 1, 2))
        test_mmap_array = self.mmaparray('i', int_array)
        assert test_mmap_array[0] == 0
        assert test_mmap_array[1] == 1
        assert test_mmap_array[2] == 2

        extend_array = array.array('i', (3, 4))
        test_mmap_array.extend(extend_array)
        assert test_mmap_array[3] == 3
        assert test_mmap_array[4] == 4

        # Can only extend with same type
        with pytest.raises(TypeError):
            test_mmap_array.extend(array.array('f'), (1.23, 3.45))

    def test_setslice(self):
        """Test that a slice can be assigned from a mmaparray"""
        import array
        int_array = array.array('i', (0, 1, 2))
        test_mmap_array = self.mmaparray('i', int_array)

        # Can't assign from types other than array types.
        # This is due to the type restrictions for those types.
        with pytest.raises(TypeError):
            test_mmap_array[1:2] = [50]

        different_type_array = self.mmaparray('f', array.array('f', (1.23,)))
        # Type of the array must be the same to do a slice assignement
        with pytest.raises(TypeError):
            test_mmap_array[1:2] = different_type_array

        assigning_array = self.mmaparray('i', array.array('i', (50,)))
        test_mmap_array[1:2] = assigning_array
        assert test_mmap_array[0] == 0
        assert test_mmap_array[1] == 50
        assert test_mmap_array[2] == 2

    def test_setslice_regression(self):
        arr = self.mmaparray('I', (1, 1, 1, 1))
        import array
        arr[2:4] = array.array('I', (2, 2))
        assert arr[0] == 1
        assert arr[1] == 1
        assert arr[2] == 2
        assert arr[3] == 2


    def test_setslice_from_array(self):
        """Test that a slice can be assigned from an array.array containing same type"""
        import array
        int_array = array.array('i', (0, 1, 2))
        test_mmap_array = self.mmaparray('i', int_array)

        assigning_array = array.array('i', (50,))
        test_mmap_array[1:2] = assigning_array
        assert test_mmap_array[0] == 0
        assert test_mmap_array[1] == 50
        assert test_mmap_array[2] == 2
