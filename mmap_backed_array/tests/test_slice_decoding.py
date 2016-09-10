"""
Tests for slice decoding
"""
import pytest

from mmap_backed_array.slice_decoding import (
    _decode_index,
    _decode_slice,
)

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

    #Step must be an integer, this is a pretty crazy edge case really
    s = slice(1,2,"step edge case")
    with pytest.raises(TypeError):
        _decode_slice(s, 10)

    s = slice(1,2,0)
    with pytest.raises(ValueError):
        _decode_slice(s, 10)

    s = slice("Bad start type",2,1)
    with pytest.raises(TypeError):
        _decode_slice(s, 10)

    s = slice(1,"Bad stop type",1)
    with pytest.raises(TypeError):
        _decode_slice(s, 10)

def test_decode_index_bad_parameter():
    """Test that bad parameters passed to decode_index raise"""
    s = slice(1,2,3)
    with pytest.raises(TypeError):
        _decode_index(s, "This is not a real size")


    #Invalid index values
    with pytest.raises(IndexError):
        _decode_index(-6, 5)

    with pytest.raises(IndexError):
        _decode_index(6, 5)

def test_decode_index_integer():
    """Test that _decode_index provides appropriate indexes into a collection"""
    
    a = [1, 2, 3]

    #We should be able to make a slice that returns the same items as a direct indexing operation
    for idx in [-2, -1, 0, 1, 2]:
        indices_info = _decode_index(idx, len(a))
        assert a[idx] == a[indices_info[0]]

def test_decode_slice():
    """Test that _decode_slice generates the correct indexes
    into a collection for given slices"""

    slice_step = 1
    test_collection = ['a', 'b', 'c', 'd']
    #We define a slice that will generate a length1 list if applied to the test collection
    s = slice(1,2,slice_step)
    indices_info = _decode_slice(s, len(test_collection))
    #start
    assert indices_info[0] == 1
    assert test_collection[indices_info[0]] == test_collection[1]
    #end
    assert indices_info[1] == 2
    assert test_collection[indices_info[1]] == test_collection[2]
    #step
    assert indices_info[2] == slice_step
    #length
    assert indices_info[3] == 1
