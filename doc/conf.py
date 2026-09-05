# urlfetch documentation build configuration file.
# Built locally with Sphinx; published to GitHub Pages.

import os
import sys

root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, root_path)

import urlfetch

extensions = ["sphinx.ext.autodoc", "sphinx.ext.viewcode"]
exclude_patterns = ["_build"]
source_suffix = {".rst": "restructuredtext"}
master_doc = "index"

project = "urlfetch"
copyright = "2011-2026, Yue Du <ifduyue@gmail.com>"
author = "Yue Du <ifduyue@gmail.com>"
version = urlfetch.__version__
release = urlfetch.__version__

language = "en"
pygments_style = "sphinx"
autodoc_member_order = "bysource"

html_theme = "alabaster"
html_theme_options = {
    "description": "An easy to use HTTP client",
    "github_user": "ifduyue",
    "github_repo": "urlfetch",
    "github_banner": True,
    "fixed_sidebar": True,
    "page_width": "960px",
}
html_static_path = ["_static"]
html_show_sourcelink = True
html_baseurl = "https://ifduyue.github.io/urlfetch/"
htmlhelp_basename = "urlfetchdoc"
