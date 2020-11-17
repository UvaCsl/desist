from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
        name="isct",
        version="0.0.1",
        packages=find_packages('isct'),
        entry_points={
            'console_scripts': [
                'isct = isct.isct:main',
            ],
        },
        install_requires=[
            'docopt',
            'PyYAML',
            'schema',
        ],
)
