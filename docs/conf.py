# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
import unittest
from pathlib import Path

# Headless builds import the plotting helpers while collecting docstrings.
os.environ.setdefault("MPLBACKEND", "Agg")

# Tests import these modules as top-level names (fp_array, cordic, ...).
_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(_SCRIPTS))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Noise-Shaping SAR PCB'
copyright = '2026, Alex Knowlton'
author = 'Alex Knowlton'
release = '0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_peakrdl",
]

# The modeling modules use NumPy-style docstrings. Napoleon also accepts
# Google style. Private helpers and dunder methods stay out unless a
# directive asks for a specific special member.
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = False

# Show FixedPointArray.__init__ parameters on the class, in source order.
autoclass_content = "both"
autodoc_member_order = "bysource"


def _skip_test_cases(app, what, name, obj, skip, options):
    """Leave unittest.TestCase classes off the generated API pages."""
    del app, what, name, skip, options
    try:
        if isinstance(obj, type) and issubclass(obj, unittest.TestCase):
            return True
    except TypeError:
        return None
    return None


def setup(app):
    app.connect("autodoc-skip-member", _skip_test_cases, priority=900)


# Path(s) to your SystemRDL file(s)
peakrdl_input_files = [
    "./hdl_design/hdl_design.srcs/registers/regblock_udps.rdl",
    "./hdl_design/hdl_design.srcs/registers/dac_registers.rdl",
    "./hdl_design/hdl_design.srcs/registers/adc_registers.rdl",
    "./hdl_design/hdl_design.srcs/registers/chip_top.rdl"
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']