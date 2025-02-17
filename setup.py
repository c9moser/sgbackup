#!/usr/bin/env python

import os
import sys
from setuptools import setup
import subprocess
import bz2

PACKAGE_ROOT=os.path.dirname(__file__)

sys.path.insert(0,PACKAGE_ROOT)
import sgbackup

setup(
    name='sgbackup',
    version=sgbackup.__version__
    description='A backup tool for savegames.',
    author="Christian Moser",
    author_email="christian@cmoser.eu",
    packages=[
        'sgbackup',
        'sgbackup.archivers',
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
