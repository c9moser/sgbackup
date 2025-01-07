# vim: syn=python ts=4 sts=4 sw=4 smartindent autoindent expandtab

import sys,os

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0,PROJECT_ROOT)
import sgbackup

project = 'sgbackup'
copyright = '2024-2025, Christian Moser'
author = 'Christian Moser'
version = sgbackup.__version__

exclude_patterns = [
    '_build',
    'Thumbs.db',
    '.DS_Store',
    '*~',
    '*.swp',
    '*.tmp',
    '*.temp',
    '*.log',
]

extensions = [
        'sphinx.ext.autodoc'
]
language = 'en'
master_doc = 'index'
source_suffix = {
        '.rst': "restructuredtext",
        '.txt': "restructuredtext",
        '.md': 'markdown',
        '.markdown': 'mardown',
}
templates_path = ['templates']

html_theme = 'sphinx_rtd_theme'
html_show_sourcelink = False
#html_static_path = ['_static']

autoclass_content='both'
autodoc_class_signature='mixed'
autodoc_default_options={
    'member_order':'alphabetical',
    'undoc_members':'true',
    'exclude_memebers':'__weakref__',
}

