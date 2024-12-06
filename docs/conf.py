import os
import sys
sys.path.insert(0, os.path.abspath('../src'))

project = 'TGBot-Logging'
copyright = '2024, Kirill Bykov'
author = 'Kirill Bykov'
release = '0.1.0'

# Internationalization settings
language = 'en'  # Default language
locale_dirs = ['locale/']  # path is example but recommended
gettext_compact = False  # optional
gettext_uuid = True  # optional

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

# Language-specific options
language_options = {
    'en': {
        'project': 'TGBot-Logging',
        'copyright': '2024, Kirill Bykov',
        'author': 'Kirill Bykov',
    },
    'ru': {
        'project': 'TGBot-Logging',
        'copyright': '2024, Кирилл Быков',
        'author': 'Кирилл Быков',
    }
}

# Set language-specific options if language is set
if language in language_options:
    for key, value in language_options[language].items():
        globals()[key] = value

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'telegram': ('https://python-telegram-bot.readthedocs.io/en/stable/', None),
}

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
    'titles_only': False
}

autodoc_member_order = 'bysource'
autodoc_typehints = 'description'
add_module_names = False 