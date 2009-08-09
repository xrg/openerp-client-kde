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

# Added so py2exe properly packs xml.etree.ElementTree
from xml.etree.ElementTree import parse, SubElement

import sys, os

if os.name == 'nt':
	sys.path.append('.')

from distutils.sysconfig import get_python_lib
terp_path = "/".join([get_python_lib(), 'Koo'])
sys.path.append(terp_path)

from Koo.Common import Localization
Localization.initializeTranslations()

from Koo.Common.Settings import Settings


from PyQt4.QtCore import *
from PyQt4.QtGui import *

from Koo.Common import Notifier, Common

# Declare notifier handlers for the whole application
Notifier.errorHandler = Common.error
Notifier.warningHandler = Common.warning
Notifier.concurrencyErrorHandler = Common.concurrencyError

### Main application loop
app = QApplication( sys.argv )
try:
	app.setStyleSheet( file(Options.options['stylesheet']).read() )
except:
	pass

Localization.initializeQtTranslations()

from Koo.Dialogs.KooMainWindow import *
from Koo.Dialogs.WindowService import *
import Koo.Actions

mainWindow = QMainWindow(None, Qt.CustomizeWindowHint)
mainWindow.setLayout( QHBoxLayout( mainWindow ) )

from Koo.Common import Api

class KooApi(Api.KooApi):
	def execute(self, actionId, data={}, type=None, context={}):
		Koo.Actions.execute( actionId, data, type, context )

	def executeReport(self, name, data={}, context={}):
		return Koo.Actions.executeReport( name, data, context )

	def executeAction(self, action, data={}, context={}):
		Koo.Actions.executeAction( action, data, context )
		
	def executeKeyword(self, keyword, data={}, context={}):
		return Koo.Actions.executeKeyword( keyword, data, context )

	def createWindow(self, view_ids, model, res_id=False, domain=None, 
			view_type='form', window=None, context=None, mode=None, name=False, autoReload=False, 
			target='current'):
		WindowService.createWindow( view_ids, model, res_id, domain, 
			view_type, window, context, mode, name, autoReload, target )

	def windowCreated(self, window, target):
		mainWindow.setCentralWidget( window )
		window.setParent( mainWindow )
		window.show()

Api.instance = KooApi()

mainWindow.showFullScreen()

import Pos
app.installEventFilter( Pos.PosEventFilter(mainWindow) )

# Load default wizard
Rpc.session.login( 'PYROLOC://admin:admin@localhost:8071', 'test' )
id = Rpc.session.execute('/object', 'execute', 'res.users', 'read', [Rpc.session.uid], ['menu_id','name'], Rpc.session.context)

# Store the menuId so we ensure we don't open the menu twice when
# calling openHomeTab()
menuId = id[0]['menu_id'][0]

Api.instance.execute(menuId)

app.exec_()

