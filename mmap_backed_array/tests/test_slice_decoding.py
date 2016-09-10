"""
Tests for slice decoding
"""
import pytest

from slice_decoding import _decode_slice

def test_decode_slice_bad_parameter():
    """Test that bad parameters to decode_slice raise"""
    with pytest.raises(TypeError):
        _decode_slice("this is not a slice object", 10)
