#!/usr/bin/env python

import os
import sys
from setuptools import setup
import subprocess
import bz2

PACKAGE_ROOT=os.path.dirname(__file__)

VERSION="0.0.1"
with open(os.path.join(PACKAGE_ROOT,'sgbackup','version.py'),'w') as version_file:
    version_file.write("""# This file was automatically created by setup.py

VERSION="{version}"
""".format(version=VERSION))

setup(
    name='sgbackup',
    version=VERSION,
    description='A backup tool for savegames.',
    author="Christian Moser",
    author_email="christian@cmoser.eu",
    packages=[
        'sgbackup',
        'sgbackup.archiver',
        'sgbackup.commands',
        'sgbackup.curses',
        'sgbackup.help',
        'sgbackup.gui',
    ],
    package_data={
        'sgbackup':[
            'icons/sgbackup.ico',
            'icons/hicolor/symbolic/*/*.svg'
        ],
        'sgbackup.gui': [
            '*.ui'
        ],
    },
    platforms=['win32','linux']
)
