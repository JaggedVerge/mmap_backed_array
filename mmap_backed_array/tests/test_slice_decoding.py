"""
Tests for slice decoding
"""
import pytest

from mmap_backed_array.slice_decoding import _decode_slice

def test_decode_slice_bad_parameter():
    """Test that bad parameters to decode_slice raise"""
    with pytest.raises(TypeError):
        _decode_slice("this is not a slice object", 10)

    s = slice(1,2,3)
    #sice must be an integer
    with pytest.raises(TypeError):
        _decode_slice(s, "This is not a real size")
    with pytest.raises(TypeError):
        _decode_slice(s, 0.12345)

    #size can't be negative
    with pytest.raises(ValueError):
        _decode_slice(s, -1)
