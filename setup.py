#!/usr/bin/env python
# -*- coding: utf-8 -*-
# setup for KTiny (taken from TinyERP GTK client)
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

name = 'ktiny'
version = '1.0.0-beta1'

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
    files = [(opj('share','man','man1',''),['man/ktiny.1']),
             #(opj('share','doc', 'ktiny-%s' % version), [f for f in glob.glob('doc/*') if os.path.isfile(f)]),
             #(opj('share', 'pixmaps', 'ktiny'), glob.glob('bin/ui/common.rcc') + glob.glob('bin/ui/*.ui')),
             #(opj('share', 'pixmaps', 'ktiny', 'icons'), glob.glob('bin/ui/images/*.png')),
             (opj('share', 'doc', 'ktiny', 'manual' ), [f for f in glob.glob('doc/html/*') if os.path.isfile(f)]),
             (opj('share', 'doc', 'ktiny', 'api' ), [f for f in glob.glob('doc/doxygen/html/*') if os.path.isfile(f)]),
             (opj('share', 'ktiny'), ['bin/tipoftheday.txt']),
	     (opj('share', 'ktiny', 'ui'), glob.glob('bin/ui/common.rcc') + glob.glob('bin/ui/*.ui')),
	     (opj('share', 'ktiny', 'ui', 'images'), glob.glob('bin/ui/images/*.png'))
	     ]
    return files

included_plugins = ['workflow_print']

def find_plugins():
    for plugin in included_plugins:
        path=opj('bin', 'plugins', plugin)
        for dirpath, dirnames, filenames in os.walk(path):
            if '__init__.py' in filenames:
                modname = dirpath.replace(os.path.sep, '.')
                yield modname.replace('bin', 'ktiny', 1)

def translations():
    trans = []
    dest = 'share/locale/%s/LC_MESSAGES/%s.mo'
    for po in glob.glob('bin/po/*.po'):
        lang = os.path.splitext(os.path.basename(po))[0]
        trans.append((dest % (lang, name), po))
    return trans

long_desc = '''\
=====================================
KTiny Client and Development Platform
=====================================

KTiny is a Qt/KDE based client for Tiny ERP, a complete ERP and CRM. KTiny
aims for great flexibility allowing easy creation of plugins and views, high
integration with KDE4 under Unix, Windows and Mac, as well as providing
a development platform for new applications using the Tiny ERP server.

A set of server side modules is also provided among the KTiny distribution
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
cd %s/ktiny
exec %s ./ktiny.py $@
""" % ( get_python_lib(), sys.executable)
# write script
f = open('ktiny', 'w')
f.write(start_script)
f.close()

# todo: use 
command = sys.argv[1]

setup(name             = name,
      version          = version,
      description      = "KTiny Client",
      long_description = long_desc,
      url              = 'http://sf.net/projects/ktiny',
      author           = 'NaN',
      author_email     = 'info@nan-tic.com',
      classifiers      = filter(None, classifiers.splitlines()),
      license          = 'GPL',
      data_files       = data_files(),
      translations     = translations(),
      pot_file         = 'bin/po/terp-msg.pot',
      scripts          = ['ktiny'],
      packages         = ['ktiny', 
                          'ktiny.common', 
                          'ktiny.modules', 
			  'ktiny.modules.action',
                          'ktiny.modules.gui',
                          'ktiny.modules.gui.window',
                          'ktiny.modules.gui.window.view_tree',
                          'ktiny.modules.spool',
                          'ktiny.printer', 
                          'ktiny.widget',
                          'ktiny.widget.model',
                          'ktiny.widget.screen',
                          'ktiny.widget.view',
                          'ktiny.widget.view.form',
                          'ktiny.widget.view.tree',
			  'ktiny.widget.view.chart',
                          'ktiny.widget_search',
			  'ktiny.rpc',
			  'ktiny.ui',
			  'ktiny.tinygraph',
                          'ktiny.plugins'] + list(find_plugins()),
      package_dir      = {'ktiny': 'bin'},
      provides         = [ 'ktiny' ]
      )


# vim:expandtab:tw=80
