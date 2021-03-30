#!/usr/bin/env python3

import re
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

package_name = "soundpad"
VERSIONFILE="%s/_version.py" % package_name
verstrline = open(VERSIONFILE, "rt").read()
VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
mo = re.search(VSRE, verstrline, re.M)
if mo:
    verstr = mo.group(1)
    print("found version %s" % verstr)
else:
    raise RuntimeError("Unable to find version string in %s." % (VERSIONFILE,))


setuptools.setup(
    name=package_name,
    version=verstr,
    author="Florian Streibelt",
    author_email="pypi@streibelt.net",
    description="A small tool to use a novation launchpad mini as soundboard.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mutax/soundpad",
    packages=setuptools.find_packages(),
    install_requires=['pygame', 'launchpad-py'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': [
            'soundpad=soundpad.soundpad:main',
        ],
    },
    python_requires='>=3.5',
)
