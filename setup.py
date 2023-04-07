from setuptools import setup, find_packages

def readme():
  with open('README.md') as f:
    return f.read()

import sys
if not sys.version_info[0] == 3:
  sys.exit("Sorry, only Python 3 is supported")

setup(name='egcwebapp',
      version='0.1',
      description='Storing and manages rules about the '+\
                  ' expected content of genomes',
      long_description=readme(),
      long_description_content_type="text/markdown",
      install_requires=[
      ],
      url='https://github.com/ggonnella/egcwebapp',
      keywords="genomes, rules, expectations",
      author='Giorgio Gonnella',
      author_email='gonnella@zbh.uni-hamburg.de',
      license='ISC',
      # see https://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Software Development :: Libraries',
      ],
      packages=find_packages(),
      scripts=[],
      zip_safe=False,
      test_suite="pytest",
      include_package_data=True,
      tests_require=['pytest', 'pytest-console-scripts'],
    )
