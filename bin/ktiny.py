#!/usr/bin/python

##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#                    Fabien Pinckaers <fp@tiny.Be>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################
"""
Tiny ERP - Client
Tiny ERP is an ERP+CRM program for small and medium businesses.

The whole source code is distributed under the terms of the
GNU Public Licence.

(c) 2003-TODAY, Fabien Pinckaers - Tiny sprl
"""
__author__ = 'Fabien Pinckaers, <fp@tiny.be>'
__version__ = "4.0.0"


import __builtin__
__builtin__.__dict__['tinyerp_version'] = __version__

import sys, os
import logging

logging.basicConfig()

if os.name == 'nt':
	sys.path.append('.')

from distutils.sysconfig import get_python_lib
terp_path = "/".join([get_python_lib(), 'ktiny'])
sys.path.append(terp_path)

import locale, gettext

# end testing
APP = 'terp'
DIR = 'po'

locale.setlocale(locale.LC_ALL, '')
gettext.bindtextdomain(APP, DIR)
gettext.textdomain(APP)
gettext.install(APP, DIR, unicode=1)

import options


for logger in options.options['logging.logger'].split(','):
	if len(logger):
		loglevel = {'DEBUG':logging.DEBUG, 'INFO':logging.INFO, 'WARNING':logging.WARNING, 'ERROR':logging.ERROR, 'CRITICAL':logging.CRITICAL}
		log = logging.getLogger(logger)
		log.setLevel(loglevel[options.options['logging.level'].upper()])
if options.options['logging.verbose']:
	logging.getLogger().setLevel(logging.INFO)
else:
	logging.getLogger().setLevel(logging.ERROR)


import modules

imports={}

from PyQt4.QtCore import *
from PyQt4.QtGui import *
try:
	import dbus.mainloop.qt
	import dbus.service
	import dbus
	imports['dbus'] = True 
except:
	imports['dbus'] = False
	print _("Module 'dbus' not available. Consider installing it so other applications can easily interact with KTiny.")
import service

from common import notifier, common

# Declare notifier handlers for the whole application
notifier.errorHandler = common.error
notifier.warningHandler = common.warning

# The TinyERPInterface gives access from DBUS to the local services.
# To test it you may simply use the following command line: 
# qdbus org.ktiny.Interface /TinyERP org.ktiny.Interface.call "gui.window" "create" "None, 'res.partner', False, [], 'form', mode='form,tree'"
#
if imports['dbus']:
	class TinyERPInterface(dbus.service.Object):
		def __init__(self, path):
			dbus.service.Object.__init__(self, dbus.SessionBus(), path)

		# This functions returns a list of available local services
		@dbus.service.method(dbus_interface='org.tinyerp.Interface', in_signature='', out_signature='as')
		def services(self):
			return service.AvailableServices()

		# This function lets execute any given function of any local service. See example above.
		@dbus.service.method(dbus_interface='org.tinyerp.Interface', in_signature='sss', out_signature='')
		def call(self, serviceName, function, parameters):
			obj = service.LocalService(serviceName)
			f = 'obj.%s(%s)' % (function, parameters) 
			eval(f)

### Main application loop
try:
	app = QApplication( sys.argv )

	# Create DBUS interface if dbus modules are available.
	# Needs to go after creating QApplication
	if imports['dbus']:
		dbus.mainloop.qt.DBusQtMainLoop(set_as_default=True)
		sessionBus = dbus.SessionBus()
		name = dbus.service.BusName("org.tinyerp.Interface", sessionBus )
		example = TinyERPInterface('/TinyERP')
	
	win = modules.gui.main.MainWindow()
	win.show()

	if options.options.rcexist:
		if options.options['tip.autostart']:
			dialog = common.TipOfTheDayDialog()
			dialog.exec_()
		else:
			win.showLoginDialog()
	app.exec_()

except KeyboardInterrupt, e:
	log = logging.getLogger('common')
	log.info(_('Closing Tiny ERP, KeyboardInterrupt'))

