#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


readme = open("README.rst").read()
history = open("HISTORY.rst").read().replace(".. :changelog:", "")

requirements = ["arrow>=0.15.6", "click>=7.1.2"]

test_requirements = [
    "pytest",
    "mypy",
    "flake8",
    "black",
    "pytest-cov",
]

setup(
    name="proj",
    version="0.2.0",
    description="A command-line manager for archiving and retrieving projects.",
    long_description=readme + "\n\n" + history,
    author="Lars Yencken",
    author_email="lars@yencken.org",
    url="https://github.com/larsyencken/proj",
    packages=["proj"],
    package_dir={"proj": "proj"},
    entry_points={"console_scripts": ["proj = proj:main"]},
    include_package_data=True,
    install_requires=requirements,
    license="BSD",
    zip_safe=False,
    keywords="proj",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    test_suite="tests",
    tests_require=test_requirements,
)
