# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath('../'))
sys.path.insert(0, os.getcwd())

project = 'voice-commander'
copyright = '2024, Spencer Phillip Young'
author = 'Spencer Phillip Young'
release = '0.0.2'

def get_ref():
    if 'READTHEDOCS_GIT_IDENTIFIER' in os.environ:
        return os.environ['READTHEDOCS_GIT_IDENTIFIER']

    return 'main'


viewcode_github_owner = 'spyoungtech'
viewcode_github_project = project
viewcode_github_ref = get_ref()

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx_autodoc_typehints',
    'viewcode',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
