"""Unit tests for the mmap backed array class.
Tests are a modified version of the pypy array unit tests."""
import sys
import py
from pytest import raises

class BaseArrayTests:
    def test_ctor_basic(self):
        assert len(self.array('B')) == 0
        assert len(self.array('i')) == 0

        raises(TypeError, self.array, 'hi')
        raises(TypeError, self.array, 1)
        raises(ValueError, self.array, 'q')
        a = self.array('B')
        assert len(a) == 0
        raises(TypeError, a.append, b'h')
        assert len(a) == 0
        raises(TypeError, a.append, 'hi')
        assert len(a) == 0
        a.append(7)
        assert a[0] == 7
        assert type(a[0]) is int
        assert len(a) == 1

        a = self.array('u')
        raises(TypeError, a.append, 7)
        raises(TypeError, a.append, b'hi')
        a.append('h')
        assert a[0] == 'h'
        assert type(a[0]) is str
        assert len(a) == 1

    def test_ctor(self):
        a = self.array('B', (1, 2, 3))
        assert a[0] == 1
        assert a[1] == 2
        assert a[2] == 3
        assert len(a) == 3

        b = self.array('B', a)
        assert len(b) == 3
        assert a == b
        raises(TypeError, self.array, 'i', a)

        a = self.array('i', (1, 2, 3))
        b = self.array('h', (1, 2, 3))
        assert a == b

    def test_ctor_typecodes(self):
        for tc in 'bhilBHILfd':
            assert self.array(tc).typecode == tc
            raises(TypeError, self.array, tc, None)

    def test_float(self):
        values = [0, 1, 2.5, -4.25]
        for tc in 'fd':
            a = self.array(tc, values)
            assert len(a) == len(values)
            for i, v in enumerate(values):
                assert a[i] == v
                assert type(a[i]) is float
            a[1] = 10.125
            assert a[0] == 0
            assert a[1] == 10.125
            assert a[2] == 2.5
            assert len(a) == len(values)


class TestArray(BaseArrayTests):
    def setup_class(cls):
        import mmap_backed_array
        cls.array = mmap_backed_array.mmaparray
        import struct
        cls.struct = struct
        cls.tempfile = str(py.test.ensuretemp('mmaparray').join('tmpfile'))
        cls.maxint = sys.maxsize #get the biggest addressable size
