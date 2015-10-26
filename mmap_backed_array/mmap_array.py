"""mmap backed array datastructure"""
import mmap as _mmap

__all__ = [
    "mmaparray",
]

class mmaparray:
    """mmap backed Array like data structure"""
    def __new__(cls, typecode, *args, **kwargs):
        """:typecode: the typecode for the underlying mmap array"""
        self = object.__new__(cls)
