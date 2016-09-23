mmap_backed_array
=================
.. image:: https://travis-ci.org/JaggedVerge/mmap_backed_array.svg
    :target: https://travis-ci.org/JaggedVerge/mmap_backed_array

.. image:: https://coveralls.io/repos/JaggedVerge/mmap_backed_array/badge.svg?branch=master&service=github
    :target: https://coveralls.io/github/JaggedVerge/mmap_backed_array?branch=master

This library lets you create arrays with mmap backing.
The interface is designed to be very similar to the array_ module in the standard library.

.. _array: https://docs.python.org/3/library/array.html

Use case
--------
This library gives you the ability to have a shared memory space between different processes.
This can be helpful to work around some of the concurrency limitations present in some Python implementations.

This library was originally created to support the usage of very large precomputed lookup tables across multiple threads/processes.
Because of the large size of these tables creating copies for each process would have been very expensive in terms of memory usage.
By creating a mmap backing and accessing read-only multiple processes could read from the same memory hence leading to memory savings.

There's also another use case when doing interprocess communications, if you want a quick-and-dirty shared memory between
processes in python and processes using other languages you can use this library to share a flat memory space between them.

If you just need some simple shared memory and don't want, or can't, bring in a more complicated dependency this might be what you need.
For more complicated concurrency tasks there may be more suitable libraries.

Usage
-----

Instantiation:
~~~~~~~~~~~~~~

If you don't provide a file for mmap backing an anonymous mmap is created to back the array.

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

API
~~~
The API is designed to be as close to the standard library array_ module API as possible.
Using mmaparray's is designed to be similar to array.array.
Another goal is to make interoperating with array.array as easy as possible.

Major functionality including (but not limited) to ``append``, ``extend``, ``pop`` and ``tobytes`` is supported.
There are some slight incompatibilities currently, for example mmaparray has a typecode property but
does not have the typecodes listing property.

For example:

.. code:: python

    arr = mmaparray('I')
    >>> arr.append(1)
    >>> arr
    array('I', [1])
    >>> arr.extend([2,3,4])
    >>> arr
    array('I', [1, 2, 3, 4])

You can also use the standard library arrays easily with the mmap backed arrays:

.. code:: python

    >>> from mmap_backed_array import mmaparray
    >>> mmap_array = mmaparray('I', (1, 1, 1, 1))
    >>> mmap_array
    array('I', [1, 1, 1, 1])
    >>> import array
    >>> mmap_array[2:4] = array.array('I', (2, 2))
    >>> mmap_array
    array('I', [1, 1, 2, 2])


Due to the way in which we are storing direct to arrays, just like in the standard library array_ the typecodes must match up:

.. code:: python

    >>> mmap_array.typecode
    'I'
    >>> mmap_array[2:4] = array.array('b', (3, 3))
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "/home/janis/mmap_backed_array/mmap_backed_array/mmap_array.py", line 302, in __setitem__
        'Can only assign array of same type to array slice'
    TypeError: Can only assign array of same type to array slice

