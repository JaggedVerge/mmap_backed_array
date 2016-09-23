from .mmap_array import *

__all__ = [mmap_array.__all__, 'typecodes']

from .mmap_array import _mmap

typecodes = "".join(list(mmap_array._typecode_to_type.keys()))

