# Configuration file for the Sphinx documentation builder.
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
from datetime import datetime

# -- Path setup --------------------------------------------------------------
# Add project root to sys.path for autodoc to find modules
sys.path.insert(0, os.path.abspath('..'))

# -- Project information -----------------------------------------------------
project = 'ctrutils'
copyright = f'{datetime.now().year}, Cristian Tacoronte Rivero'
author = 'Cristian Tacoronte Rivero'
release = '11.0.0'
version = '11.0.0'

# -- General configuration ---------------------------------------------------
extensions = [
    # Core Sphinx extensions
    'sphinx.ext.autodoc',          # Auto-generate docs from docstrings
    'sphinx.ext.napoleon',         # Support for Google/NumPy style docstrings
    'sphinx.ext.viewcode',         # Add links to highlighted source code
    'sphinx.ext.intersphinx',      # Link to other projects' documentation
    'sphinx.ext.autosummary',      # Generate summary tables
    'sphinx.ext.coverage',         # Check documentation coverage
    'sphinx.ext.githubpages',      # GitHub Pages support

    # Markdown support
    'myst_parser',                 # Parse markdown files
]

# Napoleon settings (Google-style docstrings)
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = True
napoleon_type_aliases = None
napoleon_attr_annotations = True

# Autodoc settings
autodoc_default_options = {
    'members': True,                # Include all members
    'member-order': 'bysource',     # Order by source code order
    'special-members': '__init__',  # Include __init__
    'undoc-members': False,         # Don't include undocumented members
    'exclude-members': '__weakref__, __dict__, __module__',
    'show-inheritance': True,       # Show inheritance
}
autodoc_typehints = 'description'   # Show type hints in description
autodoc_typehints_description_target = 'documented'
autodoc_mock_imports = []           # Add external dependencies if needed

# Autosummary settings
autosummary_generate = True         # Generate stub files
autosummary_imported_members = False

# Intersphinx mapping (link to external docs)
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'pandas': ('https://pandas.pydata.org/docs/', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'influxdb': ('https://influxdb-python.readthedocs.io/en/latest/', None),
}

# MyST parser settings (Markdown)
myst_enable_extensions = [
    'colon_fence',      # ::: fences
    'deflist',          # Definition lists
    'substitution',     # Variable substitution
    'tasklist',         # Task lists
]
myst_heading_anchors = 3            # Auto-generate anchors for headings

# Templates path
templates_path = ['_templates']

# Patterns to exclude
exclude_patterns = [
    '_build',
    'Thumbs.db',
    '.DS_Store',
    '**.ipynb_checkpoints',
    'tests',
]

# Source file encoding
source_encoding = 'utf-8'

# Language (for content, not UI)
language = 'es'  # Spanish content

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'     # Read the Docs theme

html_theme_options = {
    'analytics_id': '',              # Google Analytics ID (if needed)
    'logo_only': False,
    'display_version': True,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': True,
    'vcs_pageview_mode': '',
    'collapse_navigation': False,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False,
}

html_static_path = ['_static']
html_css_files = ['custom.css']

# Sidebar logo
# html_logo = '_static/logo.png'

# Favicon
# html_favicon = '_static/favicon.ico'

# Title and short title
html_title = f'{project} v{release}'
html_short_title = project

# Output file base name for HTML
htmlhelp_basename = 'ctrutilsdoc'

# Show source link
html_show_sourcelink = True
html_copy_source = True

# -- Options for other output formats ----------------------------------------

# LaTeX output (PDF)
latex_elements = {
    'papersize': 'a4paper',
    'pointsize': '10pt',
}
latex_documents = [
    ('index', 'ctrutils.tex', 'ctrutils Documentation',
     'Cristian Tacoronte Rivero', 'manual'),
]

# Manual page output
man_pages = [
    ('index', 'ctrutils', 'ctrutils Documentation',
     [author], 1)
]

# Texinfo output
texinfo_documents = [
    ('index', 'ctrutils', 'ctrutils Documentation',
     author, 'ctrutils', 'Librería minimalista de utilidades en Python.',
     'Miscellaneous'),
]

# -- Extension configuration -------------------------------------------------

# Coverage checking
coverage_show_missing_items = True
