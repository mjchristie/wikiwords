"""
Install wikiwords.
"""

try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup
	
config = {
	'description': 'Collect and compare word frequencies from Wikipedia pages',
	'author': 'Matt Christie',
	'author_email': 'mjchristie@wisc.edu',
	'version': '0.1',
	'install_requires': ['lxml', 'requests', 'beautifulsoup4'],
	'name': 'wikiwordss'
}

setup(**config)
