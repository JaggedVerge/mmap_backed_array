"""
Decoding of slice information
"""
import operator

def _decode_old_slice(i, j, size):
    """Find (start, stop, length) information that a simple slice
    represents in terms of indexes into a collection of the given size
    :i: start index
    :j: end index
    :size: the size of the collection
    """
    if i < 0:
        i = 0
    elif i > size:
        i = size
    if j < i:
        j = i
    elif j > size:
        j = size
    return i, j, j-i


def _decode_slice(s, size):
    """Find (start, stop, step, length) information that an extended slice
    represents in terms of indexes into a collection of the given size.
    Note that this function exists because slice.indices doesn't correctly decode these
    in some cases.

    :s: slice object
    :size: the size of the collection
    """
    # validate slice
    if not isinstance(s, slice):
        raise TypeError('s must be a slice object')

    # validate size
    if not isinstance(size, int):
        raise TypeError('size must be an integer')
    if size < 0:
        raise ValueError('size must not be negative')

    # validate step
    if s.step is None:
        step = 1
    elif not isinstance(s.step, int):
        raise TypeError('step must be an integer')
    else:
        step = s.step
    if step == 0:
        raise ValueError('step must not be zero')

    if step < 0:
        # validate and normalize start
        if s.start is None:
            start = size-1
        elif not isinstance(s.start, int):
            raise TypeError('start must be an integer')
        else:
            start = s.start
            if start >= size:
                start = size-1
            elif start < 0:
                start += size
                if start < 0:
                    # empty, set start=step so the reversed sequence becomes
                    # 0, 0, -step
                    start = step

        # validate and normalize stop
        if s.stop is None:
            stop = -1
        elif not isinstance(s.stop, int):
            raise TypeError('stop must be an integer')
        else:
            stop = s.stop
            if stop < 0:
                stop += size
                if stop < 0:
                    stop = -1

        # ensure that size > start >= stop >= step
        # and  start == stop (mod step)
        # by decrementing stop as necessary
        if stop > start:
            stop = start
        else:
            stop += (start-stop)%step # negative or zero, since step is negative
        assert size > start >= stop >= step

    else:
        # validate and normalize start
        if s.start is None:
            start = 0
        elif not isinstance(s.start, int):
            raise TypeError('start must be an integer')
        else:
            start = s.start
            if start >= size:
                start = size
            elif start < 0:
                start += size
                if start < 0:
                    start = 0

        # validate and normalize stop
        if s.stop is None:
            stop = size
        elif not isinstance(s.stop, int):
            raise TypeError('stop must be an integer')
        else:
            stop = s.stop
            if stop > size:
                stop = size
            elif stop < 0:
                stop += size
                if stop < 0:
                    stop = start

        # ensure that  0 <= start <= stop <= size+step
        # and  start == stop (mod step)
        # by incrementing stop as necessary
        if stop <= start:
            stop = start
        else:
            stop += (start-stop)%step # positive or zero, since step is positive
        assert 0 <= start <= stop <= size+step

    length, modulus = divmod(stop-start, step)
    assert length >= 0
    assert modulus == 0
    return start, stop, step, length


def _decode_index(index_or_slice, size):
    """Get the (start, stop, step, length) information that a simple index or a slice
    represents in terms of indexes into a collection of the given size.

    :index_or_slice: the index or slice object
    :size: the size of the collection
    """
    if not isinstance(index_or_slice, slice):
        index = operator.index(index_or_slice)
        if not isinstance(size, int):
            raise TypeError('size must be an integer')
        if index < 0:
            index += size
            if index < 0:
                raise IndexError
        elif index >= size:
            raise IndexError
        return index, 0, 0, 0
    return _decode_slice(index_or_slice, size)

