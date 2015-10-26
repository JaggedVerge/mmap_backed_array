"""mmap backed array datastructure"""
import mmap as _mmap

from cffi import FFI
ffi = FFI()

_typecode_to_type = {
    'c': ffi.typeof('char'),         'u': ffi.typeof('wchar_t'),
    'b': ffi.typeof('signed char'),  'B': ffi.typeof('unsigned char'),
    'h': ffi.typeof('signed short'), 'H': ffi.typeof('unsigned short'),
    'i': ffi.typeof('signed int'),   'I': ffi.typeof('unsigned int'),
    'l': ffi.typeof('signed long'),  'L': ffi.typeof('unsigned long'),
    'f': ffi.typeof('float'),        'd': ffi.typeof('double'),
}

__all__ = [
    "mmaparray",
]

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
