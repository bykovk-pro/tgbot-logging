import os
import sys

sys.path.insert(0, os.path.abspath("../src"))

project = "TGBot-Logging"
copyright = "2024, Kirill Bykov"
author = "Kirill Bykov"
release = "0.1.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx_rtd_theme",
    "sphinx.ext.githubpages",
    "sphinx_autodoc_typehints",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_show_sourcelink = True
html_show_sphinx = True
html_show_copyright = True

# Intersphinx mapping
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "telegram": ("https://python-telegram-bot.readthedocs.io/en/stable/", None),
}

# Theme options
html_theme_options = {
    "logo_only": False,
    "display_version": True,
    "prev_next_buttons_location": "bottom",
    "style_external_links": True,
    "style_nav_header_background": "#2980B9",
    "collapse_navigation": False,
    "sticky_navigation": True,
    "navigation_depth": 4,
    "includehidden": True,
    "titles_only": False,
}

# Autodoc settings
autodoc_member_order = "bysource"
autodoc_typehints = "description"
add_module_names = False

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_use_ivar = True
napoleon_use_param = True
napoleon_use_rtype = True

# Type hints settings
typehints_fully_qualified = False
always_document_param_types = True
typehints_document_rtype = True

# HTML settings
html_title = f"{project} v{release} documentation"
html_short_title = project
html_favicon = "_static/favicon.ico"
html_logo = "_static/logo.png"
html_css_files = [
    "custom.css",
]

# Additional settings
nitpicky = True
nitpick_ignore = [
    ("py:class", "telegram.Bot"),
    ("py:class", "telegram.error.TelegramError"),
    ("py:class", "telegram.error.RetryAfter"),
    ("py:class", "telegram.error.TimedOut"),
    ("py:class", "telegram.error.InvalidToken"),
]

# Logging settings
suppress_warnings = ["app.add_node"]

# LaTeX settings
latex_elements = {
    "preamble": r"""
    \usepackage{emoji}
    \usepackage[utf8]{inputenc}
    \DeclareUnicodeCharacter{1F535}{\emoji{large-blue-circle}}
    \DeclareUnicodeCharacter{26A0}{\emoji{warning}}
    \DeclareUnicodeCharacter{FE0F}{}
    \DeclareUnicodeCharacter{1F4AC}{\emoji{speech-balloon}}
    \DeclareUnicodeCharacter{1F3E2}{\emoji{office-building}}
    \DeclareUnicodeCharacter{1F4CD}{\emoji{round-pushpin}}
    \DeclareUnicodeCharacter{26AA}{\emoji{white-circle}}
    \DeclareUnicodeCharacter{1F7E2}{\emoji{large-green-circle}}
    \DeclareUnicodeCharacter{1F7E1}{\emoji{large-yellow-circle}}
    \DeclareUnicodeCharacter{1F534}{\emoji{red-circle}}
    \DeclareUnicodeCharacter{26D4}{\emoji{no-entry}}
    \DeclareUnicodeCharacter{1F310}{\emoji{globe-with-meridians}}
    \DeclareUnicodeCharacter{1F5C4}{\emoji{file-cabinet}}
    \DeclareUnicodeCharacter{1F4CA}{\emoji{bar-chart}}
    \DeclareUnicodeCharacter{1F680}{\emoji{rocket}}
    \DeclareUnicodeCharacter{2728}{\emoji{sparkles}}
    \DeclareUnicodeCharacter{23F0}{\emoji{alarm-clock}}
    \DeclareUnicodeCharacter{231A}{\emoji{watch}}
    \DeclareUnicodeCharacter{1F4C5}{\emoji{calendar}}
    \DeclareUnicodeCharacter{1F1EA}{\emoji{regional-indicator-e}}
    \DeclareUnicodeCharacter{1F1FA}{\emoji{regional-indicator-u}}
    \DeclareUnicodeCharacter{1F1F8}{\emoji{regional-indicator-s}}
    \DeclareUnicodeCharacter{1F4C6}{\emoji{tear-off-calendar}}
    \DeclareUnicodeCharacter{1F4DD}{\emoji{memo}}
    \DeclareUnicodeCharacter{23F3}{\emoji{hourglass-flowing-sand}}
    \DeclareUnicodeCharacter{1F50D}{\emoji{magnifying-glass-tilted-left}}
    \DeclareUnicodeCharacter{1F4BB}{\emoji{laptop}}
    \DeclareUnicodeCharacter{2699}{\emoji{gear}}
    \DeclareUnicodeCharacter{1F41B}{\emoji{bug}}
    \DeclareUnicodeCharacter{26A1}{\emoji{high-voltage}}
    \DeclareUnicodeCharacter{1F4A5}{\emoji{collision}}
    \DeclareUnicodeCharacter{1F198}{\emoji{sos}}
    \DeclareUnicodeCharacter{1F537}{\emoji{large-blue-diamond}}
    \DeclareUnicodeCharacter{2139}{\emoji{information}}
    \DeclareUnicodeCharacter{274C}{\emoji{cross-mark}}
    \DeclareUnicodeCharacter{1F6A8}{\emoji{police-car-light}}
    """,
}
