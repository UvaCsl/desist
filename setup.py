from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

_isct_packages = find_packages('isct/')

_dev = ['yapf', 'tox', 'flake8', 'numpy', 'sphinx', 'sphinx_rtd_theme']
_test = ['mock', 'pytest', 'pytest-cov', 'pytest-mock']
_vvuq = ['easyvvuq']
_all = _dev + _test + _vvuq


setup(
    name="isct",
    version="0.0.1",
    description='Streamline In Silico Computational Trials',
    author_email='m.vanderkolk@uva.nl',
    packages=_isct_packages,
    keywords=['in-silico'],
    entry_points={
        'console_scripts': [
            'isct = isct.isct:cli',
        ],
    },
    python_requires='>=3.8, <4',
    install_requires=[
        'click>=7.1.2',
        'PyYAML>=5.3',
        'schema>=0.7',
    ],
    extras_require={
        'all': _all,
        'dev': _dev,
        'test': _test,
        'vvuq': _vvuq,
    },
)
