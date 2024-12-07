import os
import sys
sys.path.insert(0, os.path.abspath('../src'))

project = 'TGBot-Logging'
copyright = '2024, Kirill Bykov'
author = 'Kirill Bykov'
release = '0.1.0'

# Internationalization settings
language = os.getenv('READTHEDOCS_LANGUAGE', 'en')
locale_dirs = ['locale']
gettext_compact = False
gettext_uuid = True
gettext_additional_targets = ['literal-block', 'image']
gettext_auto_build = True
gettext_languages = ['ru']

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'sphinx_rtd_theme',
    'sphinx.ext.githubpages',
    'sphinx_autodoc_typehints',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_show_sourcelink = True
html_show_sphinx = True
html_show_copyright = True

# Language-specific options
if language == 'ru':
    project = 'TGBot-Logging'
    copyright = '2024, Кирилл Быков'
    author = 'Кирилл Быков'

# Intersphinx mapping
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'telegram': ('https://python-telegram-bot.readthedocs.io/en/stable/', None),
}

# Theme options
html_theme_options = {
    'logo_only': False,
    'display_version': True,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': True,
    'style_nav_header_background': '#2980B9',
    'collapse_navigation': False,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False,
}

# Autodoc settings
autodoc_member_order = 'bysource'
autodoc_typehints = 'description'
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
html_favicon = '_static/favicon.ico'
html_logo = '_static/logo.png'
html_css_files = [
    'custom.css',
]

# Additional settings
nitpicky = True
nitpick_ignore = [
    ('py:class', 'telegram.Bot'),
    ('py:class', 'telegram.error.TelegramError'),
    ('py:class', 'telegram.error.RetryAfter'),
    ('py:class', 'telegram.error.TimedOut'),
    ('py:class', 'telegram.error.InvalidToken'),
]

# Logging settings
suppress_warnings = ['app.add_node']