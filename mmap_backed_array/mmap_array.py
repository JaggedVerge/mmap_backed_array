"""mmap backed array datastructure"""
import mmap
import array, os, operator

from .slice_decoding import (
    _decode_old_slice,
    _decode_index,
)


_mmap = mmap

from cffi import FFI
ffi = FFI()
ffi.cdef("""
typedef unsigned int mode_t;
int shm_open(const char *name, int oflag, mode_t mode);
int shm_unlink(const char *name);
""")
C = ffi.verify("""
#include <sys/mman.h>
""", libraries=["rt"])


_typecode_to_type = {
    'c': ffi.typeof('char'),         'u': ffi.typeof('wchar_t'),
    'b': ffi.typeof('signed char'),  'B': ffi.typeof('unsigned char'),
    'h': ffi.typeof('signed short'), 'H': ffi.typeof('unsigned short'),
    'i': ffi.typeof('signed int'),   'I': ffi.typeof('unsigned int'),
    'l': ffi.typeof('signed long'),  'L': ffi.typeof('unsigned long'),
    'f': ffi.typeof('float'),        'd': ffi.typeof('double'),
}

__all__ = [
    "anon_mmap", "C", "ffi", "mmaparray",
]

def anon_mmap(data):
    """Create an anonymous mmap that can be resized"""
    data = memoryview(data)
    size = len(data)#TODO: check that this is actually correct, might need to be data.nbytes given this is a memoryview
    name_str = '/{}'.format(os.getpid())
    name = bytes(name_str, 'ascii')
    fd = C.shm_open(name, os.O_RDWR|os.O_CREAT|os.O_EXCL, 0o600)
    if fd < 0:
        errno = ffi.errno
        raise OSError(errno, os.strerror(errno))
    try:
        if C.shm_unlink(name) != 0:
            errno = ffi.errno
            raise OSError(errno, os.strerror(errno))
        os.write(fd, data)
        result = _mmap.mmap(fd, size)
    finally:
        os.close(fd)
    return result


import ctypes
def address_of_buffer(buf):
    """Find the address of a buffer"""
    obj = ctypes.py_object(buf)
    address = ctypes.c_void_p()
    length = ctypes.c_ssize_t()
    ctypes.pythonapi.PyObject_AsReadBuffer(obj, ctypes.byref(address), ctypes.byref(length))
    return address.value


class mmaparray:
    """mmap backed Array like data structure"""
    def __new__(cls, typecode, *args, **kwargs):
        """:typecode: the typecode for the underlying mmap array"""
        self = object.__new__(cls)

        # Validate the typecode provided
        if not isinstance(typecode, str) or len(typecode) != 1:
            raise TypeError
        try:
            itemtype = _typecode_to_type[typecode]
        except KeyError:
            raise ValueError
        self._itemtype = itemtype
        self._typecode = typecode
        self._ptrtype = ffi.typeof(ffi.getctype(itemtype, '*'))
        self._itemsize = ffi.sizeof(itemtype)

        # validate *args
        if len(args) > 1:
            raise TypeError("expected 1 or 2 arguments, got %d" % (1+len(args)))
        if len(args) == 1:
            data = args[0]
            iter(data) # verify that args is iterable
        else:
            data = None

        # validate **kwargs
        mmap = kwargs.pop('mmap', None)
        if kwargs:
            raise TypeError("unexpected keyword arguments %r" % kwargs.keys())

        # handle default mmap, validate and store mmap, compute size
        if mmap is None:
            mmap = anon_mmap(b'\x00')
            size = 0
        elif not isinstance(mmap, _mmap.mmap):
            raise TypeError("expected an mmap instance, got %r" % mmap)
        else:
            size = len(mmap)
            size -= size % self.itemsize
        self._mmap = mmap
        self._setsize(size)

        #append the data
        if data is not None:
            if isinstance(data, bytes):
                self._frombytes(data)
            elif isinstance(data, str):
                self._fromstring(data)
            elif isinstance(data, array.array):
                if data.typecode == typecode:
                    self._frombytes(memoryview(data))
                else:
                    raise TypeError("Typecodes must be the same")
            elif isinstance(data, mmaparray):
                if data.typecode == typecode:
                    self._from_mmaparray(data)
                else:
                    raise TypeError("Typecodes must be the same")
            else:
                data = array.array(typecode, data)
                self._frombytes(memoryview(data))

        return self

    def _setsize(self, size):
        """Set the size of the mmap object"""
        self._size = size
        self._length = size//self._itemsize
        pointer_to_beginning_of_mmap_buffer = address_of_buffer(self._mmap)
        self._data = ffi.cast(self._ptrtype, pointer_to_beginning_of_mmap_buffer)

    def _resize(self, size):
        """Resize the mmap object
        :size: new size
        """
        assert size >= 0
        if size == 0:
            self._mmap.resize(1)
            #self._mmap[0] = b'\x00' #This gives a typeerror in cpython 3.4
            self._mmap[0] = 0
        else:
            self._mmap.resize(size)
        self._setsize(size)


    #Array API
    def __add__(self, other):
        result = mmaparray(self.typecode, self)
        try:
            result.extend(other)
        except TypeError:
            return NotImplemented
        return result

    def __copy__(self):
        return mmaparray(self.typecode, self)

    def __eq__(self, other):
        try:
            return (self is other or
                    all(x == y for x, y in zip(self, other))
                    )
        except TypeError:
            return NotImplemented

    def __ge__(self, other):
        if self is not other:
            for x, y in zip(self, other):
                if x == y:
                    continue
                return x > y
        return True

    def __getitem__(self, index):
        if isinstance(index, int):
            if index < 0:
                index += self._length
                if index < 0:
                    raise IndexError
            elif index >= self._length:
                raise IndexError
            return self._data[index]
        start, stop, step = index.indices(self._length)
        if step == 0:
            return self._data[start]
        elif step == 1:
            return array.array(
                self.typecode,
                self._data[start:stop],
                )
        else:
            return array.array(
                self.typecode,
                (self._data[i] for i in range(start, stop, step)),
                )

    def __getslice__(self, i, j):
        start, stop, length = _decode_old_slice(i, j, self._length)
        return array.array(self.typecode, self._data[start:stop])

    def __gt__(self, other):
        for x, y in zip(self, other):
            if x == y:
                continue
            return x > y
        return False


    def __iadd__(self, other):
        try:
            self.extend(other)
        except TypeError:
            return NotImplemented
        return self

    def __imul__(self, other):
        if not isinstance(other, int):
            return NotImplemented
        if other <= 0:
            self._resize(0)
        elif other > 1:
            size = self._size
            self._resize(other*size)
            newsize = self._size
            while size < newsize:
                rest = newsize-size
                if rest < size:
                    self._mmap.move(size, 0, rest)
                    break
                else:
                    self._mmap.move(size, 0, size)
                    size += size
        return self

    def __le__(self, other):
        if self is not other:
            for x, y in zip(self, other):
                if x == y:
                    continue
                return x < y
        return True

    def __len__(self):
        return self._length

    def __lt__(self, other):
        for x, y in zip(self, other):
            if x == y:
                continue
            return x < y
        return False

    def __mul__(self, other):
        if not isinstance(other, int):
            return NotImplemented
        print("__mul__ called")
        if other > 0:
            result = mmaparray(self.typecode, self)
            result *= other
        else:
            result = mmaparray(self.typecode)
        return result
    def __repr__(self):
        data = array.array(self.typecode, self._tobytes())
        return repr(data)

    __rmul__ = __mul__

    def __setitem__(self, index, value):
        if isinstance(index, int):
            if index < 0:
                index += self._length
                if index < 0:
                    raise IndexError
            elif not index < self._length:
                raise IndexError
            self._data[index] = value
            return
        start, stop, step, length_of_slice = _decode_index(index, self._length)
        assert length_of_slice >= 0

        if step == 0:
            self._data[start] = value
            return

        if not isinstance(value, (array.array, mmaparray)):
            raise TypeError(
                    'Can only assign array (not "{}" to array slice'.format(type(value).__name__)
                )
        if value.typecode != self.typecode:
            raise TypeError(
                'Can only assign array of same type to array slice'
                )
        if step == 1:
            self._set_simple_slice(start, stop, length_of_slice, value)
        else: #extended slice, must be of same length
            if len(value) != length_of_slice:
                raise ValueError('attempt to assign object of length %r '
                                 'to extended slice of length %r'
                                 % (len(value), length_of_slice))
            for i,v in zip(range(start, stop, step), value):
                self._data[i] = v

    def __setslice__(self, i, j, value):
        # validate value
        if not isinstance(value, (array.array, mmaparray)):
            raise TypeError(
                'can only assign array (not "%s") to array slice'
                % type(value).__name__
                )
        if value.typecode != self.typecode:
            raise TypeError(
                'can only assign array of same kind to array slice'
                )

        start, stop, length = _decode_old_slice(i, j, self._length)
        self._set_simple_slice(start, stop, length, value)

    def _set_simple_slice(self, start, stop, length, value):
        # resize if necessary
        size = self._size
        newlength = len(value)
        movesize = (newlength-length)*self.itemsize
        pos = stop*self.itemsize
        if newlength > length:
            # need to expand first, then move
            self._resize(size+movesize)
            self._mmap.move(pos+movesize, pos, size-pos)
        elif newlength < length:
            # need to move first, then shrink
            self._mmap.move(pos+movesize, pos, size-pos)
            self._resize(size+movesize)

        # then copy values over as a single block
        startpos = start*self.itemsize
        stoppos = (start+newlength)*self.itemsize
        if isinstance(value, mmaparray):
            ffi.cast("char*", self._data)[startpos:stoppos] = value.tobytes()
        else:
            ffi.cast("char*", self._data)[startpos:stoppos] = value.tobytes()#Can this be done with memoryview?
            #ffi.cast("char*", self._data)[startpos:stoppos] = memoryview(value)


    def _frombytes(self, data):
        """Fill the mmap array from a bytes datasource
        :data: the data
        """
        if isinstance(data, memoryview):
            bytesize = data.nbytes
        else:
            bytesize = len(data)
        if bytesize%self.itemsize != 0:
            raise ValueError
        if bytesize:
            pos = self._size
            assert pos % self.itemsize == 0
            self._resize(pos+bytesize)
            if isinstance(data, bytes):
                ffi.cast("char*", self._data)[pos:pos+bytesize] = data
            else:
                ffi.cast("char*", self._data)[pos:pos+bytesize] = ffi.from_buffer(data)

    frombytes = _frombytes

    def _fromstring(self, data):
        if not isinstance(data, str):
            raise TypeError
        if self.typecode != 'u':
            raise ValueError
        bytes_encoded = data.encode('utf-32le') #Do we need to check that ffi.sizeof('wchar_t') == 4 first?
        self._frombytes(bytes_encoded)
    fromstring = _fromstring

    def _from_mmaparray(self, data):
        """Fill the mmap array from another mmap array object by appending it to the end of the current array.
        :data: mmaparray object
        """
        if not isinstance(data, mmaparray):
            raise TypeError
        if self.typecode != data.typecode:
            raise TypeError("Typecodes must be the same, got %s and %s" % (self.typecode, data.typecode))
        othersize = data._size
        if othersize%self.itemsize != 0:
            raise ValueError
        if othersize:
            pos = self._size
            bytes_from_data = data.tobytes()#Note this must be called before resizing.
                                            #otherwise bytes will be the wrong length in cases such as
                                            #a._from_mmaparray(a) or  a.extend(a) if a is the mmaparray type
            #TODO: Can this be done better?
            self._resize(pos + othersize)
            #TODO: Check that this gets the underlying memory from the other mmaparray object correctly
            ffi.cast("char*", self._data)[pos:pos+othersize] = bytes_from_data


    def append(self, x):
        """Append an item to the Array
        :x: the item to append
        """
        pos = self._size
        assert pos % self.itemsize == 0
        try:
            self._resize(pos+self.itemsize)
            self._data[pos//self.itemsize] = x
        except TypeError:
            self._resize(pos)
            raise

    def buffer_info(self):
        """Tuple of address, length of the array"""
        return address_of_buffer(self._mmap), self._size

    def byteswap(self):
        """Swap the byte order of the array."""
        if self.itemsize == 1:
            return
        if self.itemsize not in (2,4,8):
            raise RuntimeError
        for pos in range(0, self._size, self.itemsize):
            self._mmap[pos:pos+self.itemsize] = self._mmap[pos:pos+self.itemsize][::-1]

    def count(self, x):
        """Return the number of occurrences of the given item in the array.
        :x: the item we are counting in the array
        """
        return sum(x==y for y in self)

    def extend(self, items):
        """Append items to the end of the array
        :items: items to append
        """
        if isinstance(items, array.array):
            if items.typecode != self.typecode:
                raise TypeError('can only extend with array of same kind')
            self._frombytes(memoryview(items))
        elif isinstance(items, mmaparray):
            if items.typecode != self.typecode:
                raise TypeError('can only extend with array of same kind')
            self._from_mmaparray(items)
        else:
            data = array.array(self.typecode)
            try:
                data.extend(items)
            finally:
                if data:
                    self._frombytes(memoryview(data))

    def _fromfile(self, f, n):
        """Read in data from a file
        :f: the file
        :n: size to read
        """
        readsize = n*self.itemsize
        data = f.read(readsize)
        datasize = len(data)
        if datasize < readsize:
            datasize -= datasize%self.itemsize
            if datasize:
                self._frombytes(data[:datasize])
            raise EOFError #didn't get the whole file, need to try again?
        self._frombytes(data)
    fromfile = _fromfile


    def fromlist(self, items):
        """Append items from the list."""
        data = array.array(self.typecode)
        data.fromlist(items)
        if data:
            self._frombytes(memoryview(data))
    _fromlist = fromlist

    def index(self, x):
        """Return the smallest i such that i is the index of the first occurrence of x in the array."""
        for i, y in enumerate(self):
            if y == x:
                return i
        raise ValueError

    def insert(self, i, x):
        """Insert a new item with value x in the array before position i.
        Negative values are treated as being relative to the end of the array."""
        i = operator.index(i)
        stop = self._length
        if i < 0:
            i += stop
            if i < 0:
                i = 0
        elif i > stop:
            i = stop
        size = self._size
        assert size % self.itemsize == 0
        self._resize(size+self.itemsize)
        if i < stop:
            pos = i*self.itemsize
            self._mmap.move(pos+self.itemsize, pos, size-pos)
        self._data[i] = x

    def pop(self, i=-1):
        """Remove the item with the index i and return it.
        Optional argument defaults to -1 which will remove the last element."""
        i = operator.index(i)
        stop = self._length
        if i < 0:
            i += stop
            if i < 0:
                raise IndexError
        elif not i < stop:
            raise IndexError
        x = self._data[i]
        pos = i*self.itemsize
        size = self._size
        assert size%self.itemsize == 0
        next_pos = pos+self.itemsize
        if next_pos < size:
            self._mmap.move(pos, next_pos, size-next_pos)
        self._resize(size-self.itemsize)
        return x

    def remove(self, x):
        """Remove the first occurence of x from the array"""
        self.pop(self.index(x))

    def reverse(self):
        """Reverse the order of the items in the array."""
        stop = self._length
        end = stop-1
        for i in range(stop//2):
            j = end-i
            tmp = self._data[i]
            self._data[i] = self._data[j]
            self._data[j] = tmp

    def tolist(self):
        """Convert the array to an ordinary list with the same items."""
        return list(self)
    _tolist = tolist

    def tostring(self):
        """
        Deprecated.
        Returns a bytes object representing the array.
        Note that this is an alias of tobytes method
        """
        return self.tobytes()#make this an alias for tobytes like cpython >3.2 ?
    _tostring = tostring

    def tobytes(self):
        """Returns a bytes object representing the array."""
        return bytes(ffi.buffer(self._data, self._length * self._itemsize))
    _tobytes = tobytes

    def tounicode(self):
        """Return a regular python3 (unicode) string"""
        if self.typecode != 'u':
            # Note array.array raises ValueError in this case
            raise ValueError("tounicode() may only be called on unicode type arrays")
        return self._tobytes().decode('utf-32le') #Do we need to check that ffi.sizeof('wchar_t') == 4 first?
    _tounicode = tounicode

    itemsize = property(operator.attrgetter('_itemsize'))
    typecode = property(operator.attrgetter('_typecode'))
