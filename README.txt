Matt Christie, 2015-2016

This is a tiny tool that lets the user play with word frequencies from
Wikipedia pages.

### Installation ###

$ mkvirtualenv wikiwords
$ cd /just/within/the/folder/wikiwords
$ pip install -r requirements.txt
$ python setup.py install

Notes:

Don't rely on the setup script to correctly install dependencies; 
use pip directly with the requirements file.

The above uses virtualenvwrapper; using just virtualenv or no virtual
environment at all should work just fine too, although the exact commands
will look a little different (you'll need to add sudo in front of the
last two commands if you're not using a virtual environment). Google
pip, virtualenv, and virtualenvwrapper for more details.

### Generating Data ###

$ # Judge page similarity randomly from a list of pages
$ python -m wikiwords judge -f pages.txt
$ 
$ # Judge a pages's similarity against two other pages
$ python -m wikiwords judge --pages Tree Plant Hollywood
$ 
$ # Save a page's word frequencies to a file
$ python -m wikiwords save -p Old_English -d word_frequencies
$ 
$ # Compare word frequencies obtained from parsing different parts of a page
$ python -m wikiwords compare -p Old_English --parsers raw body
$ 
$ # help/full specification of commands
$ python -m wikiwords -h
$ python -m wikiwords <command-name> -h

An example of a file to pass to judge -f is included in this directory
as pages.txt.

