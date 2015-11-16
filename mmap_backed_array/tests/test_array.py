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

    def test_value_range(self):
        import sys
        values = (-129, 128, -128, 127, 0, 255, -1, 256,
                  -32768, 32767, -32769, 32768, 65535, 65536,
                  -2147483647, -2147483648, 2147483647, 4294967295, 4294967296,
                  )
        for bb in (8, 16, 32, 64, 128, 256, 512, 1024):
            for b in (bb - 1, bb, bb + 1):
                values += (2 ** b, 2 ** b + 1, 2 ** b - 1,
                           -2 ** b, -2 ** b + 1, -2 ** b - 1)

        for tc, ok, pt in (('b', (  -128,    34,   127),  int),
                           ('B', (     0,    23,   255),  int),
                           ('h', (-32768, 30535, 32767),  int),
                           ('H', (     0, 56783, 65535),  int),
                           ('i', (-32768, 30535, 32767),  int),
                           ('I', (     0, 56783, 65535), int),
                           ('l', (-2 ** 32 // 2, 34, 2 ** 32 // 2 - 1),  int),
                           ('L', (0, 3523532, 2 ** 32 - 1), int),
                           ):
            a = self.array(tc, ok)
            assert len(a) == len(ok)
            for v in ok:
                a.append(v)
            for i, v in enumerate(ok * 2):
                assert a[i] == v
                assert type(a[i]) is pt or (
                    # A special case: we return ints in Array('I') on 64-bits,
                    # whereas CPython returns longs.  The difference is
                    # probably acceptable.
                    tc == 'I' and
                    sys.maxint > 2147483647 and type(a[i]) is int)
            for v in ok:
                a[1] = v
                assert a[0] == ok[0]
                assert a[1] == v
                assert a[2] == ok[2]
            assert len(a) == 2 * len(ok)
            for v in values:
                try:
                    a[1] = v
                    assert a[0] == ok[0]
                    assert a[1] == v
                    assert a[2] == ok[2]
                except OverflowError:
                    pass

        for tc in 'BHIL':
            a = self.array(tc)
            vals = [0, 2 ** a.itemsize - 1]
            a.fromlist(vals)
            assert a.tolist() == vals

            a = self.array(tc.lower())
            vals = [-1 * (2 ** a.itemsize) // 2,  (2 ** a.itemsize) // 2 - 1]
            a.fromlist(vals)
            assert a.tolist() == vals

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

    def test_itemsize(self):
        for t in 'cbB':
            assert(self.array(t).itemsize >= 1)
        for t in 'uhHiI':
            assert(self.array(t).itemsize >= 2)
        for t in 'lLf':
            assert(self.array(t).itemsize >= 4)
        for t in 'd':
            assert(self.array(t).itemsize >= 8)

        inttypes = 'bhil'
        for t in inttypes:
            a = self.array(t, [1, 2, 3])
            b = a.itemsize
            for v in (-2 ** (8 * b) // 2, 2 ** (8 * b) // 2 - 1):
                print(type(v))
                a[1] = v
                assert a[0] == 1 and a[1] == v and a[2] == 3
            raises(OverflowError, a.append, -2 ** (8 * b) // 2 - 1)
            raises(OverflowError, a.append, 2 ** (8 * b) // 2)

            a = self.array(t.upper(), [1, 2, 3])
            b = a.itemsize
            for v in (0, 2 ** (8 * b) - 1):
                a[1] = v
                assert a[0] == 1 and a[1] == v and a[2] == 3
            raises(OverflowError, a.append, -1)
            raises(OverflowError, a.append, 2 ** (8 * b))

    def test_frombytes(self):
        a = self.array('c')
        a.frombytes(b'Hi!')
        assert a[0] == b'H' and a[1] == b'i' and a[2] == b'!' and len(a) == 3

        for t in 'bBhHiIlLfd':
            a = self.array(t)
            a.frombytes(b'\x00' * a.itemsize * 2)
            assert len(a) == 2 and a[0] == 0 and a[1] == 0
            if a.itemsize > 1:
                raises(ValueError, a.frombytes, b'\x00' * (a.itemsize - 1))
                raises(ValueError, a.frombytes, b'\x00' * (a.itemsize + 1))
                raises(ValueError, a.frombytes, b'\x00' * (2 * a.itemsize - 1))
                raises(ValueError, a.frombytes, b'\x00' * (2 * a.itemsize + 1))
            b = self.array(t, b'\x00' * a.itemsize * 2)
            assert len(b) == 2 and b[0] == 0 and b[1] == 0

    def test_fromfile(self):
        def myfile(c, s):
            f = open(self.tempfile, 'wb')
            f.write(c * s)
            f.close()
            return open(self.tempfile, 'rb')

        f = myfile(b'\x00', 100)
        for t in 'bBhHiIlLfd':
            a = self.array(t)
            a.fromfile(f, 2)
            assert len(a) == 2 and a[0] == 0 and a[1] == 0

        a = self.array('b')
        a.fromfile(myfile(b'\x01', 20), 2)
        assert len(a) == 2 and a[0] == 1 and a[1] == 1

        a = self.array('h')
        a.fromfile(myfile(b'\x01', 20), 2)
        assert len(a) == 2 and a[0] == 257 and a[1] == 257

        for i in (0, 1):
            a = self.array('h')
            raises(EOFError, a.fromfile, myfile(b'\x01', 2 + i), 2)
            assert len(a) == 1 and a[0] == 257

    def test_fromlist(self):
        a = self.array('b')
        raises(OverflowError, a.fromlist, [1, 2, 400])
        assert len(a) == 0

        raises(OverflowError, a.extend, [1, 2, 400])
        assert len(a) == 2 and a[0] == 1 and a[1] == 2

        raises(OverflowError, self.array, 'b', [1, 2, 400])

        a = self.array('b', [1, 2])
        assert len(a) == 2 and a[0] == 1 and a[1] == 2

        a = self.array('b')
        raises(TypeError, a.fromlist, (1, 2, 400))

        raises(OverflowError, a.extend, (1, 2, 400))
        assert len(a) == 2 and a[0] == 1 and a[1] == 2

        raises(TypeError, a.extend, self.array('i', (7, 8)))
        assert len(a) == 2 and a[0] == 1 and a[1] == 2

        def gen():
            for i in range(4):
                yield i + 10
        a = self.array('i', gen())
        assert len(a) == 4 and a[2] == 12

        raises(OverflowError, self.array, 'b', (1, 2, 400))

        a = self.array('b', (1, 2))
        assert len(a) == 2 and a[0] == 1 and a[1] == 2

        a.extend(a)
        assert repr(a) == "array('b', [1, 2, 1, 2])"

    def test_fromstring(self):
        raises(ValueError, self.array('i').fromstring, 'hi')
        a = self.array('u')
        a.fromstring('hi')
        assert len(a) == 2 and a[0] == 'h' and a[1] == 'i'

        b = self.array('u', 'hi')
        assert len(b) == 2 and b[0] == 'h' and b[1] == 'i'


    def test_type(self):
        for t in 'bBhHiIlLfdcu':
            assert type(self.array(t)) is self.array
            assert isinstance(self.array(t), self.array)


    def test_list_methods(self):
        assert repr(self.array('i')) == "array('i')"
        assert repr(self.array('i', [1, 2, 3])) == "array('i', [1, 2, 3])"
        assert repr(self.array('h')) == "array('h')"

        a = self.array('i', [1, 2, 3, 1, 2, 1])
        assert a.count(1) == 3
        assert a.count(2) == 2
        assert a.index(3) == 2
        assert a.index(2) == 1
        raises(ValueError, a.index, 10)

        a.reverse()
        assert repr(a) == "array('i', [1, 2, 1, 3, 2, 1])"

        b = self.array('i', [1, 2, 3, 1, 2])
        b.reverse()
        assert repr(b) == "array('i', [2, 1, 3, 2, 1])"

        a.remove(3)
        assert repr(a) == "array('i', [1, 2, 1, 2, 1])"
        a.remove(1)
        assert repr(a) == "array('i', [2, 1, 2, 1])"

        a.pop()
        assert repr(a) == "array('i', [2, 1, 2])"

        a.pop(1)
        assert repr(a) == "array('i', [2, 2])"

        a.pop(-2)
        assert repr(a) == "array('i', [2])"

        a.insert(1, 7)
        assert repr(a) == "array('i', [2, 7])"
        a.insert(0, 8)
        a.insert(-1, 9)
        assert repr(a) == "array('i', [8, 2, 9, 7])"

        a.insert(100, 10)
        assert repr(a) == "array('i', [8, 2, 9, 7, 10])"
        a.insert(-100, 20)
        assert repr(a) == "array('i', [20, 8, 2, 9, 7, 10])"

    def test_compare(self):
        for v1, v2, tt in (([1, 2, 3], [1, 3, 2], 'bhilBHIL'),
                         (b'abc', b'acb', 'c'),
                         ('abc', 'acb', 'u')):
            for t in tt:
                a = self.array(t, v1)
                b = self.array(t, v1)
                c = self.array(t, v2)

                assert (a == 7) is False

                assert (a == a) is True
                assert (a == b) is True
                assert (b == a) is True
                assert (a == c) is False
                assert (c == a) is False

                assert (a != a) is False
                assert (a != b) is False
                assert (b != a) is False
                assert (a != c) is True
                assert (c != a) is True

                assert (a < a) is False
                assert (a < b) is False
                assert (b < a) is False
                assert (a < c) is True
                assert (c < a) is False

                assert (a > a) is False
                assert (a > b) is False
                assert (b > a) is False
                assert (a > c) is False
                assert (c > a) is True

                assert (a <= a) is True
                assert (a <= b) is True
                assert (b <= a) is True
                assert (a <= c) is True
                assert (c <= a) is False

                assert (a >= a) is True
                assert (a >= b) is True
                assert (b >= a) is True
                assert (a >= c) is False
                assert (c >= a) is True


    def test_to_various_type(self):
        """Tests for methods that convert to other types"""
        a = self.array('i', [1, 2, 3])
        l = a.tolist()
        assert type(l) is list and len(l) == 3
        assert a[0] == 1 and a[1] == 2 and a[2] == 3


class TestArray(BaseArrayTests):
    def setup_class(cls):
        import mmap_backed_array
        cls.array = mmap_backed_array.mmaparray
        import struct
        cls.struct = struct
        cls.tempfile = str(py.test.ensuretemp('mmaparray').join('tmpfile'))
        cls.maxint = sys.maxsize #get the biggest addressable size
