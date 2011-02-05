#!/usr/bin/env python
# -*- coding: utf-8 -*-
# setup for Koo (taken from OpenERP GTK client)
#   taken from straw http://www.nongnu.org/straw/index.html
#   taken from gnomolicious http://www.nongnu.org/gnomolicious/
#   adapted by Nicolas Évrard <nicoe@altern.org>

import imp
import sys
import os
import glob
import shutil

from stat import ST_MODE

from distutils.file_util import copy_file
from distutils.sysconfig import get_python_lib

if len(sys.argv) < 2:
	print "Syntax: setup.py command [options]"
	sys.exit(2)

command = sys.argv[1]

if command == 'py2app': 
	from setuptools import setup
else:
	from distutils.core import setup

try:
	import py2exe

	# Override the function in py2exe to determine if a dll should be included
        dllList = ['mfc90.dll','msvcp90.dll','qtnetwork.pyd',
                   'qtxmlpatterns4.dll','qtsvg4.dll']
        # Required by enchant
        dllList += [
		'libglib-2.0-0.dll','libgthread-2.0-0.dll',
		'libgobject-2.0-0.dll','libgdk-win32-2.0-0.dll',
		'libgio-2.0-0.dll','libgtk-win32-2.0-0.dll',
		'libgdk_pixbuf-2.0-0.dll','libcairo-2.dll',
		'libpango-1.0-0.dll','libgio-2.0-2.dll',
	]
	origIsSystemDLL = py2exe.build_exe.isSystemDLL
        def isSystemDLL(pathname):
		if os.path.basename(pathname).lower() in dllList:
			return 0
		return origIsSystemDLL(pathname)
	py2exe.build_exe.isSystemDLL = isSystemDLL
	using_py2exe = True
except:
	using_py2exe = False
	pass

opj = os.path.join

name = 'koo'

from Koo.Common import Version
version = Version.Version

# get python short version
py_short_version = '%s.%s' % sys.version_info[:2]

required_modules = [
	('PyQt4.QtCore', 'Qt4 Core python bindings'),
	('PyQt4.QtGui', 'Qt4 Gui python bindings'),
	('PyQt4.uic', 'Qt4 uic python bindings'),
	('PyQt4.QtWebKit', 'Qt4 WebKit python bindings')
]

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
	files = [
		(opj('share','man','man1',''),[ opj('man','koo.1')]),
		(opj('share', 'doc', 'koo', 'manual' ), [f for f in glob.glob(opj('doc','html','*')) if os.path.isfile(f)]),
		(opj('share', 'doc', 'koo', 'api' ), [f for f in glob.glob(opj('doc','doxygen','html','*')) if os.path.isfile(f)]),
		(opj('share', 'Koo', 'ui'), glob.glob( opj('Koo','ui','*.ui') ) ),
		(opj('share', 'Koo', 'l10n'), glob.glob( opj('Koo','l10n','*.qm')) ),
		(opj('share', 'Koo', 'ui'), [ opj('nsis','koo-icon.png') ] ),
		(opj('share', 'Koo', 'certs'), glob.glob( opj('ssl-certs','*')) ),
	]
	if using_py2exe:
                # Add NanScan files
                files.append( (opj('share','NanScan'), ['c:\\python26\\lib\\site-packages\\NanScan\\ScanDialog.ui']) )
                files.append( (opj('share','NanScan'), ['c:\\python26\\lib\\site-packages\\NanScan\\Common.rcc']) )

		dest = opj('share','locale','%s','LC_MESSAGES')
		for src in glob.glob( opj('Koo','l10n','*','LC_MESSAGES','koo.mo') ):
			lang = src.split(os.sep)[2]
			files.append( ( (dest % lang), [src] ) )
			
		files.append(
			(opj('share','Koo','Plugins','RemoteHelp','data'), glob.glob( opj('Koo','Plugins','RemoteHelp','data','*')) ),
		)

		try:
			import enchant
			files += enchant.utils.win32_data_files()
		except:                                       
			pass
	elif command == 'py2app':
		#files.append('lib.xml')
		pass
	return files

def findPluginsDir( module ):
	result = []
	plugins = [x for x in glob.glob( opj('Koo', module,'*') ) if os.path.isdir(x)]
	for plugin in plugins:
		for dirpath, dirnames, filenames in os.walk(plugin):
			if '__init__.py' in filenames:
				result.append( dirpath )
	return result
	
def findPlugins( module ):
	return [x.replace(os.path.sep, '.') for x in findPluginsDir( module )]

long_desc = '''\
=====================================
Koo Client and Development Platform
=====================================

Koo is a Qt/KDE based client for Open ERP, a complete ERP and CRM. Koo 
aims for great flexibility allowing easy creation of plugins and views, high
integration with KDE4 under Unix, Windows and Mac, as well as providing
a development platform for new applications using the Open ERP server.

A set of server side modules is also provided among the Koo distribution
which provide better attachments handling and full text search capabilities.
'''

classifiers = """\
Development Status :: 5 - Production/Stable
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
if os.name != 'nt':
	if sys.platform == 'darwin':
		script_name = 'koo.sh'
	else:
		script_name = 'koo'

	start_script = """\
if [ -d '%s/Koo' ]; then
	cd %s/Koo
else
	# Hack for Ubuntu
	export PYTHONPATH=/usr/lib/python2.6/site-packages
	cd /usr/lib/python2.6/site-packages/Koo
fi
exec %s ./koo.py $@\n""" % ( 
		get_python_lib(), get_python_lib(), sys.executable
	)
	# write script
	f = open(script_name, 'w')
	f.write(start_script)
	f.close()
	
	script_files = [script_name]
else:
	script_files = []

packages = [
	'Koo', 
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
	'Koo.Fields',
        ] + findPlugins('Plugins') + findPlugins('View') + findPlugins('Fields') + findPlugins('Search')

if command == 'py2app':
	setup_requires = ['py2app']
else:
	setup_requires = ''

setup (
	name             = name,
	version          = version,
	description      = "Koo Client",
	long_description = long_desc,
	url              = 'http://www.NaN-tic.com/koo-platform',
	author           = 'NaN',
	author_email     = 'info@nan-tic.com',
	classifiers      = filter(None, classifiers.splitlines()),
	license          = 'GPL',
        data_files       = data_files(),
	scripts          = script_files,
	windows          = [{
                                'script': opj('Koo','koo.py'),
                                'icon_resources': [(1, opj("nsis", "koo.ico"))],
                            },{
                                'script': opj('Koo','koopos.py'),
                                'icon_resources': [(1, opj("nsis", "koo.ico"))],
			    }],
	#console          = ['Koo/koo.py'],
	packages         = packages,
	package_dir      = {'Koo': 'Koo'},
	provides         = [ 'Koo' ],
	app		 = ['Koo/koo.py'],
	options          = { 
		'py2exe': {
                        'includes': [
				'sip',
				'PyQt4.QtNetwork',
				'PyQt4.QtWebKit',
				] + packages + 
				# Required by enchant
				[
				'pango',
				'atk',
				'gobject',
				'cairo',
				],
			# Required by enchant
			'excludes': [
				'Tkinter',
				'tcl',
				'TKconstants'
			],
			# Required by enchant
			'dll_excludes': [
				'icon.dll','intl.dll','libatk-1.0-0.dll',
				'libgdk_pixbuf-2.0-0.dll','libgdk-win32-2.0-0.dll',
				'libglib-2.0-0.dll','libgmodule-2.0-0.dll',
				'libgobject-2.0-0.dll','libgthread-2.0-0.dll',
				'libgtk-win32-2.0-0.dll','libpango-1.0-0.dll',
				'libpangowin32-1.0-0.dll','wxmsw26uh_vc.dll',
				'libgio-2.0-0.dll','libcairo-2.dll',
			],
		},
		'py2app': {
			'argv_emulation': True,
			'includes': ['sip'] +  packages
		}
	},
	setup_requires	= setup_requires
)
# Without a invalid qt.conf file, Qt will try to load plugins from the system Qt instead of the packaged Qt.
# Mixing Qt versions causes things to go wrong
if command == 'py2app':
	shutil.copyfile('qt.conf','dist/%s.app/Contents/Resources/qt.conf' % name)
