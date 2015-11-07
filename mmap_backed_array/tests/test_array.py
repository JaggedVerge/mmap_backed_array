"""Unit tests for the mmap backed array class.
Tests are a modified version of the pypy array unit tests."""
import sys
import py
from pytest import raises

class BaseArrayTests:
    def test_ctor(self):
        assert len(self.array('c')) == 0
        assert len(self.array('i')) == 0

        raises(TypeError, self.array, 'hi')
        raises(TypeError, self.array, 1)
        raises(ValueError, self.array, 'q')
        a = self.array('c')
        assert len(a) == 0
        raises(TypeError, a.append, 7)
        assert len(a) == 0
        raises(TypeError, a.append, 'hi')
        assert len(a) == 0
        a.append(b'h')
        assert a[0] == b'h'
        assert type(a[0]) is bytes
        assert len(a) == 1

        a = self.array('u')
        raises(TypeError, a.append, 7)
        raises(TypeError, a.append, b'hi')
        a.append('h')
        assert a[0] == 'h'
        assert type(a[0]) is str
        assert len(a) == 1

        a = self.array('c', (b'a', b'b', b'c'))
        assert a[0] == b'a'
        assert a[1] == b'b'
        assert a[2] == b'c'
        assert len(a) == 3

        b = self.array('c', a)
        assert len(b) == 3
        assert a == b
        raises(TypeError, self.array, 'i', a)

        a = self.array('i', (1, 2, 3))
        b = self.array('h', (1, 2, 3))
        assert a == b

        for tc in 'bhilBHILfd':
            assert self.array(tc).typecode == tc
            raises(TypeError, self.array, tc, None)

        a = self.array('i', (1, 2, 3))
        b = self.array('h', a)
        assert list(b) == [1, 2, 3]


class TestArray(BaseArrayTests):
    def setup_class(cls):
        import mmap_backed_array
        cls.array = mmap_backed_array.mmaparray
        import struct
        cls.struct = struct
        cls.tempfile = str(py.test.ensuretemp('mmaparray').join('tmpfile'))
        cls.maxint = sys.maxsize #get the biggest addressable size
