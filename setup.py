#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r") as fh:
    requirements = fh.read().splitlines()

setuptools.setup(
    name="LabExT_Simulation",
    version="0.0.1",
    author="Malte Wächter",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/maltewae/LabExT_Simulation",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': [
            'LabExT-Simulation = labext_simulation.__main__:main',
        ],
    },
)
