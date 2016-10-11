from setuptools import setup

setup(name='mmap_backed_array',
      version='0.3.1',
      description='Arrays with mmap backing',
      long_description=open('README.rst').read(),
      url='https://github.com/JaggedVerge/mmap_backed_array',
      author='Janis Lesinskis',
      author_email='janis@jaggedverge.com',
      license='GPLv3',
      packages=['mmap_backed_array'],
      classifiers = [
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'Programming Language :: Python',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
      ],
      keywords='mmap array',
      install_requires=['cffi'],
)
