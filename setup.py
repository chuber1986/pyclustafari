#!/usr/bin/env python

"""The setup script."""

from setuptools import find_packages, setup

with open("README.md") as readme_file:
    readme = readme_file.read()

with open("CHANGELOG.md") as history_file:
    history = history_file.read()

requirements: list[str] = []

test_requirements = [
    "bump2version>=1.0.1",
    "pre-commit>=2.12.0",
    "tox>=3.20.1",
    "tox-conda>=0.2.0",
    "pytest-runner>=6.0.0",
    "pytest>=7.2.0",
    "pytest_cov>=4.0.0",
    "flake8>=5.0.4",
    "black>=22.10.0",
    "mypy>=0.982",
    "mkdocs>=1.4.2",
    "mkdocs-include-markdown-plugin>=3.9.1",
    "mkdocs-material>=8.5.8",
    "mkdocstrings[python]>=0.19.0",
    "mkdocs-autorefs>=0.4.1",
]

setup(
    author="Christian Huber",
    author_email="hiddenaddress@gmail.com",
    python_requires=">=3.11",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.11",
    ],
    description="Runs Python function on a cluster.",
    install_requires=requirements,
    license="MIT license",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords="clustafari",
    name="clustafari",
    packages=find_packages(include=["clustafari", "clustafari.*"]),
    package_data={"": ["../CHANGELOG.md"]},
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/chuber1986/pyclustafarai",
    version="0.1.0",
    zip_safe=False,
)
