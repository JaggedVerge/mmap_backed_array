mmap_backed_array
=================
.. image:: https://travis-ci.org/JaggedVerge/mmap_backed_array.svg
    :target: https://travis-ci.org/JaggedVerge/mmap_backed_array

.. image:: https://coveralls.io/repos/JaggedVerge/mmap_backed_array/badge.svg?branch=master&service=github
    :target: https://coveralls.io/github/JaggedVerge/mmap_backed_array?branch=master

This library lets you create arrays with mmap backing.
The interface is very similar to the array_ module in the standard library.
You can construct mmap arrays from the standard library arrays.

.. _array: https://docs.python.org/3/library/array.html

Usage
-----
If you don't provide a mmap backing an anonymous mmap is created to back the array.

.. code:: python

    import mmap_backed_array
    arr = mmap_backed_array.mmaparray('I', [1, 2, 3, 4])

You can also provide a mmap file as backing.

.. code:: python

    import mmap_backed_array
    import mmap
    with open("mmap_file", 'rb') as fd:
        mmap_backing = mmap.mmap(
                fd.fileno(), 0, access=mmap.ACCESS_READ
            )
        arr = mmap_backed_array.mmaparray('I', mmap=mmap_backing)

Note that this file can be shared with other processes, including ones
that are not python.
