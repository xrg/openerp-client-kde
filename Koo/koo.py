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

from Koo.Common.Settings import Settings
from Koo.Common import CommandLine
from Koo.Common import Localization
Localization.initializeTranslations()
#__builtins__._ = lambda x: x
CommandLine.parseArguments(sys.argv)
Localization.initializeTranslations(Settings.value('client.language'))


imports={}

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from Koo.Common import Notifier, Common
from Koo.Common import DBus

# Declare notifier handlers for the whole application
Notifier.errorHandler = Common.error
Notifier.warningHandler = Common.warning
Notifier.concurrencyErrorHandler = Common.concurrencyError




### Main application loop
if Common.isKdeAvailable:
	from PyKDE4.kdecore import ki18n, KAboutData, KCmdLineArgs
	from PyKDE4.kdeui import KApplication

	appName     = "Koo"
	catalog     = ""
	programName = ki18n ("Koo")
	version     = "1.0"
	description = ki18n ("KDE OpenObject Client")
	license     = KAboutData.License_GPL
	copyright   = ki18n ("(c) 2009 Albert Cervera i Areny")
	text        = ki18n ("none")
	homePage    = "www.nan-tic.com"
	bugEmail    = "albert@nan-tic.com"
	 
	aboutData   = KAboutData (appName, catalog, programName, version, description,
				license, copyright, text, homePage, bugEmail)

	KCmdLineArgs.init (sys.argv, aboutData)
	 
	app = KApplication ()
else:
	app = QApplication( sys.argv )

app.setApplicationName( 'Koo' )
app.setOrganizationDomain( 'www.nan-tic.com' )
app.setOrganizationName( 'NaN' )

try:
	app.setStyleSheet( file(Settings.value('stylesheet')).read() )
except:
	pass

DBus.init()

Localization.initializeQtTranslations(Settings.value('client.language'))


from Koo.Dialogs.KooMainWindow import *
from Koo.Dialogs.WindowService import *
import Koo.Actions

win = KooMainWindow()

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
		win.addWindow( window, target )

Api.instance = KooApi()

win.show()

if Settings.value('pos_mode'):
        import Pos
	app.installEventFilter( Pos.PosEventFilter(win) )

if Settings.value('tip.autostart'):
	dialog = Common.TipOfTheDayDialog()
	dialog.exec_()

win.showLoginDialog()
app.exec_()
