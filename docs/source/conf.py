# Agregar la carpeta raiz del proyecto al path
import os
import sys

sys.path.insert(0, os.path.abspath("../.."))

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "ctrutils"
copyright = "2024, Cristian Tacoronte Rivero"
author = "Cristian Tacoronte Rivero"
release = "1.0.2"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx_autodoc_typehints",
    "autoapi.extension",
    "sphinx.ext.viewcode",
    "myst_parser",
    "sphinx.ext.napoleon",
    "sphinx_copybutton",
    "sphinx.ext.autosectionlabel",
    "sphinx_design",
]

autoapi_type = "python"
autoapi_dirs = ["../../ctrutils"]
autoapi_ignore = ["*InfluxdbConnection*", "*InfluxdbUtils*"]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

language = "es"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]
