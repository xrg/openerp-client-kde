#!/usr/bin/env python
# -*- coding: utf-8 -*-
# setup for Koo (taken from TinyERP GTK client)
#   taken from straw http://www.nongnu.org/straw/index.html
#   taken from gnomolicious http://www.nongnu.org/gnomolicious/
#   adapted by Nicolas Évrard <nicoe@altern.org>

import imp
import sys
import os
import glob

from stat import ST_MODE

from distutils.file_util import copy_file
from distutils.sysconfig import get_python_lib
from mydistutils import setup

try:
	import py2exe
except:
	pass

opj = os.path.join

name = 'koo'
version = '1.0.0-beta2'

# get python short version
py_short_version = '%s.%s' % sys.version_info[:2]

required_modules = [('PyQt4.QtCore', 'Qt4 Core python bindings'),
                    ('PyQt4.QtGui', 'Qt4 Gui python bindings'),
                    ('PyQt4.uic', 'Qt4 uic python bindings')]

def check_modules():
    ok = True
    for modname, desc in required_modules:
        try:
            exec('import %s' % modname)
        except ImportError:
            ok = False
            print 'Error: python module %s (%s) is required' % (modname, desc)

    if not ok:
        sys.exit(1)

def data_files():
    '''Build list of data files to be installed'''
    files = [(opj('share','man','man1',''),['man/koo.1']),
             (opj('share', 'doc', 'koo', 'manual' ), [f for f in glob.glob('doc/html/*') if os.path.isfile(f)]),
             (opj('share', 'doc', 'koo', 'api' ), [f for f in glob.glob('doc/doxygen/html/*') if os.path.isfile(f)]),
             (opj('share', 'koo'), ['Koo/kootips.txt']),
	     (opj('share', 'koo', 'ui'), glob.glob('Koo/ui/common.rcc') + glob.glob('Koo/ui/*.ui')),
	     (opj('share', 'koo', 'ui', 'images'), glob.glob('Koo/ui/images/*.png'))
	     ]
    return files

included_plugins = ['workflow_print']

def find_plugins():
    for plugin in included_plugins:
        path=opj('Koo', 'Plugins', plugin)
        for dirpath, dirnames, filenames in os.walk(path):
            if '__init__.py' in filenames:
                yield dirpath.replace(os.path.sep, '.')
 

def translations():
    trans = []
    dest = 'share/locale/%s/LC_MESSAGES/%s.mo'
    for po in glob.glob('Koo/l10n/*.po'):
        lang = os.path.splitext(os.path.basename(po))[0]
        trans.append((dest % (lang, name), po))
    return trans

long_desc = '''\
=====================================
Koo Client and Development Platform
=====================================

Koo is a Qt/KDE based client for Tiny ERP, a complete ERP and CRM. Koo 
aims for great flexibility allowing easy creation of plugins and views, high
integration with KDE4 under Unix, Windows and Mac, as well as providing
a development platform for new applications using the Tiny ERP server.

A set of server side modules is also provided among the Koo distribution
which provide better attachments handling and full text search capabilities.
'''

classifiers = """\
Development Status :: 4 - Beta
License :: OSI Approved :: GNU General Public License (GPL)
Programming Language :: Python
Topic :: Desktop Environment :: K Desktop Environment (KDE)
Operating System :: Microsoft :: Windows
Operating System :: POSIX
Operating System :: MacOS
Topic :: Office/Business
"""

check_modules()

# create startup script
start_script = """
cd %s/Koo
exec %s ./koo.py $@
""" % ( get_python_lib(), sys.executable)
# write script
f = open('koo.py', 'w')
f.write(start_script)
f.close()

# todo: use 
command = sys.argv[1]

print "PLUGINS: ", find_plugins()
setup(name             = name,
      version          = version,
      description      = "Koo Client",
      long_description = long_desc,
      url              = 'http://sf.net/projects/ktiny',
      author           = 'NaN',
      author_email     = 'info@nan-tic.com',
      classifiers      = filter(None, classifiers.splitlines()),
      license          = 'GPL',
      data_files       = data_files(),
      translations     = translations(),
      pot_file         = 'Koo/l10n/koo.pot',
      scripts          = ['koo.py'],
      packages         = ['Koo', 
                          'Koo.Actions', 
                          'Koo.Common', 
			  'Koo.Dialogs',
			  'Koo.KooChart',
			  'Koo.Model',
			  'Koo.Plugins',
			  'Koo.Printer',
			  'Koo.Rpc',
			  'Koo.Screen',
			  'Koo.Search',
			  'Koo.View',
			  'Koo.View.Calendar',
			  'Koo.View.Chart',
			  'Koo.View.Form',
			  'Koo.View.Svg',
			  'Koo.View.Tree',
                          ] + list(find_plugins()),
      package_dir      = {'Koo': 'Koo'},
      provides         = [ 'Koo' ]
      )


# vim:expandtab:tw=80
