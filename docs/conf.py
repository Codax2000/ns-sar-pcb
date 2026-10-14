# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Noise-Shaping SAR PCB'
copyright = '2026, Alex Knowlton'
author = 'Alex Knowlton'
release = '0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx_peakrdl",
]

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