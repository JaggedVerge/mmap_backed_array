from setuptools import setup

setup(name='mmap_backed_array',
      version='0.1.0',
      description='mmap backed Array for Python',
      long_description=open('README.rst').read(),
      url='https://github.com/JaggedVerge/mmap_backed_array',
      packages=['mmap_backed_array'],
      classifiers = [
          'Development Status :: 3 - Alpha',
          'Intended Audience :: Developers',
          'Programming Language :: Python',
      ],
      keywords='mmap array',
      install_requires=['cffi'],
)
