#!/usr/bin/python

##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#                    Fabien Pinckaers <fp@tiny.Be>
# Copyright (c) 2007-2008 Albert Cervera i Areny <albert@nan-tic.com>
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

import sys, os
import logging

logging.basicConfig()

if os.name == 'nt':
	sys.path.append('.')

from distutils.sysconfig import get_python_lib
terp_path = "/".join([get_python_lib(), 'Koo'])
sys.path.append(terp_path)

from Koo.Common import Localization
Localization.initializeTranslations()

from Koo.Common import Options


for logger in Options.options['logging.logger'].split(','):
	if len(logger):
		loglevel = {'DEBUG':logging.DEBUG, 'INFO':logging.INFO, 'WARNING':logging.WARNING, 'ERROR':logging.ERROR, 'CRITICAL':logging.CRITICAL}
		log = logging.getLogger(logger)
		log.setLevel(loglevel[Options.options['logging.level'].upper()])
if Options.options['logging.verbose']:
	logging.getLogger().setLevel(logging.INFO)
else:
	logging.getLogger().setLevel(logging.ERROR)


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
	print _("Module 'dbus' not available. Consider installing it so other applications can easily interact with Koo.")
imports['dbus'] = False

from Koo.Common import Notifier, Common

# Declare notifier handlers for the whole application
Notifier.errorHandler = Common.error
Notifier.warningHandler = Common.warning
Notifier.concurrencyErrorHandler = Common.concurrencyError



# The OpenErpInterface gives access from DBUS to local api.
# To test it you may simply use the following command line: 
# qdbus org.openerp.Interface /OpenERP org.openerp.Interface.call "gui.window" "create" "None, 'res.partner', False, [], 'form', mode='form,tree'"
#
if imports['dbus']:
	class OpenErpInterface(dbus.service.Object):
		def __init__(self, path):
			dbus.service.Object.__init__(self, dbus.SessionBus(), path)

		# This function lets execute any given function of any local service. See example above.
		@dbus.service.method(dbus_interface='org.openerp.Interface', in_signature='sss', out_signature='')
		def call(self, serviceName, function, parameters):
			obj = service.LocalService(serviceName)
			f = 'obj.%s(%s)' % (function, parameters) 
			eval(f)

### Main application loop
app = QApplication( sys.argv )
try:
	app.setStyleSheet( file(Options.options['stylesheet']).read() )
except:
	pass

class KeyboardWidget(QWidget):
	def __init__(self, parent=None):
		QWidget.__init__(self, parent)
		from PyQt4.uic import loadUi
		loadUi( Common.uiPath('keyboard.ui'), self )
		self.connect( self.pushEscape, SIGNAL('clicked()'), self.escape )
		self.setWindowFlags( Qt.Popup )
		self.setWindowModality( Qt.ApplicationModal )
		pos = parent.mapToGlobal( parent.pos() )
		self.move( pos.x(), pos.y() + parent.height() )
		self.show()

	def escape(self):
		self.hide()

class PosEventFilter(QObject):
	def __init__(self, parent=None):
		QObject.__init__(self, parent)

	def eventFilter(self, obj, event):
		if event.type() != QEvent.FocusIn:
			return QObject.eventFilter( self, obj, event )

		if obj.inherits( 'QLineEdit' ):
			keyboard = KeyboardWidget( obj )
			print "QLineEdit"
		return QObject.eventFilter( self, obj, event )

#app.installEventFilter( PosEventFilter(app) )




Localization.initializeQtTranslations()

# Create DBUS interface if dbus modules are available.
# Needs to go after creating QApplication
if imports['dbus']:
	dbus.mainloop.qt.DBusQtMainLoop(set_as_default=True)
	sessionBus = dbus.SessionBus()
	name = dbus.service.BusName("org.openerp.Interface", sessionBus )
	example = OpenErpInterface('/OpenERP')

from Koo.Dialogs.KooMainWindow import *
from Koo.Dialogs.WindowService import *
import Actions

win = KooMainWindow()

from Koo.Common import Api

class KooApi(Api.KooApi):
	def execute(self, actionId, data={}, type=None, context={}):
		Actions.execute( actionId, data, type, context )

	def executeReport(self, name, data={}, context={}):
		return Actions.executeReport( name, data, context )

	def executeAction(self, action, data={}, context={}):
		Actions.executeAction( action, data, context )
		
	def executeKeyword(self, keyword, data={}, context={}):
		return Actions.executeKeyword( keyword, data, context )

	def createWindow(self, view_ids, model, res_id=False, domain=None, 
			view_type='form', window=None, context=None, mode=None, name=False, autoReload=False):
		WindowService.createWindow( view_ids, model, res_id, domain, 
			view_type, window, context, mode, name, autoReload )

	def windowCreated(self, window):
		win.addWindow( window )

Api.instance = KooApi()

win.show()

# The DebugEventFilter class has been used to find a problem with an invisible
# widget that was created, not inserted in any layout and that didn't allow to 
# click widgets below it. I'm leaving the code by now as it might be useful in the
# future. Simply uncommenting the installEventFilter line will do.
class DebugEventFilter(QObject):
	def __init__(self, parent=None):
		QObject.__init__(self, parent)
		
	def eventFilter(self, obj, event):
		print "EVENT %d THROWN ON OBJECT '%s' OF TYPE '%s'" % ( event.type(), unicode(obj.objectName() ), unicode(obj.staticMetaObject.className()) )
		return QObject.eventFilter( self, obj, event )
		

#app.installEventFilter( DebugEventFilter(win) )

if Options.options.rcexist:
	if Options.options['tip.autostart']:
		dialog = Common.TipOfTheDayDialog()
		dialog.exec_()
	else:
		win.showLoginDialog()
app.exec_()

