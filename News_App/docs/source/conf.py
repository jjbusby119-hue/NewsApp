import os
import sys
import django


sys.path.insert(0, os.path.abspath('../../'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'News_App.settings')
django.setup()

project = 'News App'
copyright = '2026, Joshua Busby'
author = 'Joshua Busby'
release = '1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    ]

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
