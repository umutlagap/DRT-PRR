"""
Setup script for the DRT-PRR package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="drt-prr",
    version="1.0.0",
    author="Umut Lagap",
    author_email="umut.lagap.21@ucl.ac.uk",
    description="Digital Risk Twin for Post-Disaster Response and Recovery",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/drt-prr",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: GIS",
    ],
    python_requires=">=3.8",
    install_requires=[
        "mesa>=2.0.0",
        "pandas>=1.5.0",
        "numpy>=1.21.0",
        "scipy>=1.9.0",
        "openpyxl>=3.0.0",
    ],
    extras_require={
        "viz": ["matplotlib>=3.5.0"],
        "geo": ["geopandas>=0.12.0", "shapely>=2.0.0"],
        "all": [
            "matplotlib>=3.5.0",
            "geopandas>=0.12.0",
            "shapely>=2.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "drt-prr=drt_prr.cli:main",
        ],
    },
)
