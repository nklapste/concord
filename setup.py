#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""concord setup.py"""

import codecs
import os
import re
import sys

from setuptools import setup, find_packages
from setuptools.command.test import test


def find_version(*file_paths):
    with codecs.open(os.path.join(os.path.abspath(os.path.dirname(__file__)), *file_paths), "r") as fp:
        version_file = fp.read()
    m = re.search(r"^__version__ = \((\d+), ?(\d+), ?(\d+)\)", version_file, re.M)
    if m:
        return "{}.{}.{}".format(*m.groups())
    raise RuntimeError("Unable to find a valid version")


VERSION = find_version("concord", "__init__.py")


class Pylint(test):
    user_options = [('pylint-args=', 'a', "Arguments to pass to pylint")]

    def initialize_options(self):
        test.initialize_options(self)
        self.pylint_args = "concord --persistent=y --rcfile=.pylintrc --output-format=colorized"

    def run_tests(self):
        import shlex
        # import here, cause outside the eggs aren't loaded
        from pylint.lint import Run
        Run(shlex.split(self.pylint_args))


class PyTest(test):
    user_options = [("pytest-args=", "a", "Arguments to pass to pytest")]

    def initialize_options(self):
        test.initialize_options(self)
        self.pytest_args = "-v --cov={}".format("concord")

    def run_tests(self):
        import shlex
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(shlex.split(self.pytest_args))
        sys.exit(errno)


def readme():
    with open("README.rst", encoding="utf-8") as f:
        return f.read()


setup(
    name="concord",
    version=VERSION,
    description="Tool to scrape and analyze Discord servers",
    long_description=readme(),
    author="Nathan Klapstein",
    author_email="nklapste@ualberta.ca",
    url="https://github.com/nklapste/concord",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
    ],
    packages=find_packages(exclude=["test"]),
    include_package_data=True,
    install_requires=[
        "discord.py",
        "flask",
        "flask-restplus",
        "dash",
        "dash-html-components",
        "dash-core-components",
        "dash-table",
    ],
    tests_require=[
        "pytest>=4.1.0,<5.0.0",
        "pytest-cov>=2.6.1,<3.0.0",
        "pylint>=2.2.2,<3.0.0",
    ],
    entry_points={
        "console_scripts": [
            "concord-server = concord.server.__main__:main",
        ],
    },
    cmdclass={"test": PyTest, "lint": Pylint},
)
