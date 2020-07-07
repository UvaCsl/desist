from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
        name="isct",
        version="0.0.1",
        packages=find_packages('workflow'),
        entry_points={
            'console_scripts': [
                'isct = workflow.isct:main',
            ],
        },
)
