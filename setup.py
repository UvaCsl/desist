from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

_desist_packages = find_packages()

# Sufficient to evaluate `pytest`.
_test = ['mock', 'pytest', 'pytest-cov', 'pytest-mock']

# Additional requirements for formatting and doc generation.
_dev = _test + [
    'yapf', 'tox', 'flake8', 'pydocstyle', 'numpy', 'sphinx',
    'sphinx_rtd_theme', 'sphinxcontrib-napoleon', 'sphinx_click'
]

_vvuq = ['easyvvuq']
_qcg = ['qcg-pilotjob']

_all = _dev + _test + _vvuq + _qcg

setup(
    name="desist",
    version="0.1.0",
    description='Streamline In Silico Computational Trials',
    author_email='m.vanderkolk@uva.nl',
    packages=_desist_packages,
    keywords=['in-silico'],
    entry_points={
        'console_scripts': [
            'desist = desist.cli.cli:cli',
        ],
    },
    python_requires='>=3.8, <4',
    install_requires=[
        'click>=7.1.2',
        'PyYAML>=5.3',
    ],
    extras_require={
        'all': _all,
        'dev': _dev,
        'test': _test,
        'vvuq': _vvuq,
        'qcg': _qcg
    },
)
