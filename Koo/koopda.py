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

# Note that we need translations in order to parse command line arguments
# because we might have to print information to the user. However, koo's
# language configuration is stored in the .rc file users might provide in 
# the command line.
#
# To solve this problem we load translations twice: one before command line
# parsing and another one after, with the definitive language.
#
# Under windows, loading language twice doesn't work, and the first one loaded
# will be the one used so we first load settings from default file and registre,
# then load translations based on that file, then parse command line arguments
# and eventually load definitive translations (which windows will ignore silently).
Settings.loadFromFile()
Settings.loadFromRegistry()
Localization.initializeTranslations(Settings.value('client.language'))

arguments = CommandLine.parseArguments(sys.argv)

Localization.initializeTranslations(Settings.value('client.language'))


imports={}

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from Koo.Common import Notifier, Common
from Koo.Common import DBus

## @brief The KeyPressEventFilter class provides an eventFilter that allows
# removes KeyPress events and sends them only when KeyRelease is received. This can be used as a workaround
# for a strange bug found when using koopda from a RDP client from a PDA.
#
# To install it in an application use 'app.installEventFilter( Koo.Common.KeyPressEventFilter( mainWindow ) )'
#
# In koopda.py we found that in some circumstances barcodes were not read properly. For 
# example the following code '00121/1' was read as '00112/1'. Investigation showed the 
# problem was not responsibility of Windows CE applications nor xrdp server. For some 
# reason some key press events were being received by koopos.py application in the 
# following way: 0 press, 0 release, 0 press, 0 release, 1 press, 1 release, **1 press**, 
# 2 press, 2 release, 1 release, / press, / release, 1 press, 1 release. As it can be seen 
# **1 press** was received before 2.
#
# The only way found to solve the issue has been to create an event filter called KeyPressEventFilter 
# in koopda.py, which drops key presses and resends them only when release event is received.
#
class KeyPressEventFilter(QObject):
	## @brief Creates a new KeyPressEventFilter object.
	def __init__(self, parent=None):
		QObject.__init__(self, parent)

	def eventFilter(self, target, event):
		if event.type() == QEvent.KeyPress:
			try:
				if event.force:
					return False
			except:
				return True
		if event.type() == QEvent.KeyRelease:
			newEvent = QKeyEvent( QEvent.KeyPress, event.key(), event.modifiers(), event.text(), event.isAutoRepeat(), event.count() )
			newEvent.force = True
			QApplication.sendEvent( target, newEvent )
		return QObject.eventFilter( self, target, event )	

class PosMessageBox(QWidget):
	def __init__(self, title, message, parent):
		QWidget.__init__(self, parent)


		self.uiTitle = QLabel( self )
		self.uiTitle.setWordWrap( True )
		self.uiTitle.setText( title )
		self.uiMessage = QLabel( self )
		self.uiMessage.setWordWrap( True )
		self.uiMessage.setText( '<b>%s</b>' % message )
		self.pushOk = QPushButton( self )
		self.pushOk.setText( _('Ok') )
		self.pushOk.setIcon( QIcon( ':/images/ok.png' ) )
		self.connect( self.pushOk, SIGNAL('clicked()'), self.accepted)

		self.layout = QVBoxLayout( self )
		self.layout.setAlignment( Qt.AlignCenter )
		self.layout.addWidget( self.uiTitle )
		self.layout.addStretch( 5 )
		self.layout.addWidget( self.uiMessage )
		self.layout.addStretch( 10 )
		self.layout.addWidget( self.pushOk )

		self.previous = mainWindow.centralWidget()
		# We need to make a little trick so that current widget
		# is not destroyed when we replace it as the central widget.
		self.previous.setParent( self )
		self.previous.hide()

		mainWindow.setCentralWidget( self )
		mainWindow.show()

	def accepted(self):
		self.previous.show()
		self.previous.setParent( None )
		mainWindow.setCentralWidget( self.previous )
		mainWindow.show()
		

def messageBox(title, message):
	dialog = PosMessageBox( title, message, mainWindow )

def handleError(title, message, details=''):
	messageBox( title, message )

def handleWarning(title, message):
	messageBox( title, message )

def handleConcurrency(model, id, context):
	pass

# Declare notifier handlers for the whole application
Notifier.errorHandler = handleError
Notifier.warningHandler = handleWarning
Notifier.concurrencyErrorHandler = handleConcurrency



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

	KCmdLineArgs.init (arguments, aboutData)
	 
	app = KApplication ()
else:
	app = QApplication( arguments )

app.setApplicationName( 'Koo POS' )
app.setOrganizationDomain( 'www.NaN-tic.com' )
app.setOrganizationName( 'NaN' )

try:
	f = open( Settings.value('koo.stylesheet'), 'r' )
	try:
		app.setStyleSheet( f.read() )
	finally:
		f.close()
except:
	pass

Localization.initializeQtTranslations(Settings.value('client.language'))


from Koo.Dialogs.KooMainWindow import *
from Koo.Dialogs.WindowService import *
import Koo.Actions

mainWindow = QMainWindow(None, Qt.CustomizeWindowHint)

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
#mainWindow.setFixedSize( 240, 320 )
#mainWindow.setFixedSize( 240, 280 )
#mainWindow.show()

if Settings.value('koo.pos_mode'):
        import Koo.Pos
	app.installEventFilter( Koo.Pos.PosEventFilter(mainWindow) )

if Settings.value('koo.enter_as_tab'):
	from Koo.Common import EnterEventFilter
	app.installEventFilter( EnterEventFilter.EnterEventFilter(mainWindow) )

from Koo.Common import ArrowsEventFilter
app.installEventFilter( ArrowsEventFilter.ArrowsEventFilter(mainWindow) )

from Koo.Common import WhatsThisEventFilter
app.installEventFilter( WhatsThisEventFilter.WhatsThisEventFilter(mainWindow) )

app.installEventFilter( KeyPressEventFilter(mainWindow) )

# Load default wizard
if not Settings.value( 'login.url'):
	sys.exit( "Error: No connection parameters given." )
if not Settings.value( 'login.db'):
	sys.exit( "Error: No database given." )

Rpc.session.login( Settings.value('login.url'), Settings.value('login.db') )

if not Rpc.session.logged():
	sys.exit( "Error: Invalid credentials." )

id = Rpc.session.execute('/object', 'execute', 'res.users', 'read', [Rpc.session.uid], ['action_id','name'], Rpc.session.context)

# Store the menuId so we ensure we don't open the menu twice when
# calling openHomeTab()
menuId = id[0]['action_id'][0]

Api.instance.execute(menuId)

app.exec_()

