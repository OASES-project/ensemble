from setuptools import setup
import os

packages = []
root_dir = os.path.dirname(__file__)
if root_dir:
    os.chdir(root_dir)

for dirpath, dirnames, filenames in os.walk('ensemble'):
    # Ignore dirnames that start with '.'
    if '__init__.py' in filenames:
        pkg = dirpath.replace(os.path.sep, '.')
        if os.path.altsep:
            pkg = pkg.replace(os.path.altsep, '.')
        packages.append(pkg)


def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join('..', path, filename))
    return paths


setup(
    name='ensemble',
    version="0.0.dev1",
    packages=packages,
    author="OASES team",
    author_email="cmutel@gmail.com",  # TODO
    license=open('LICENSE').read(),
    package_data={'ensemble': package_files(os.path.join('ensemble', 'data'))},
    entry_points = {
        'console_scripts': [
            'ensemble-cli = ensemble.bin.ensemble_cli:main',
        ]
    },
    install_requires=[
        'docopt',
        'lxml',
        'numpy',
        'pandas',
        'pyprind',
        'pysut',
        'pytest',
        'stats_arrays',
        'wrapt',
    ],
    url="https://example.com/",  # TODO
    long_description=open('README.md').read(),
    description='Open source linking for life cycle assessment',
    classifiers=[
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Scientific/Engineering :: Mathematics',
        'Topic :: Scientific/Engineering :: Visualization',
    ],
)
