#!/usr/bin/python
#############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#					Fabien Pinckaers <fp@tiny.Be>
# Copyright (c) 2007 Angel Alvarez <angel@nan-tic.com>
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


import time
import os
import gettext

import rpc

from window import windowservice, win_preference, win_full_text_search
from DatabaseCreationDialog import DatabaseCreationDialog
from DatabaseDialog import DatabaseDialog
import re
import base64

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import * 

from ServerConfigurationDialog import *
from LoginDialog import * 
from AdministratorPasswordDialog import *

from Common import options
from Common import common
from Common import api
from Common import viewsettings

class MainTabWidget(QTabWidget):
	def __init__(self, parent=None):
		QTabWidget.__init__(self, parent)
		self.pressedAt = -1

	def mousePressEvent(self, event):
		if event.button() == Qt.MidButton:
			self.pressedAt = self.tabBar().tabAt( event.pos() )
	
	def mouseReleaseEvent(self, event):
		if event.button() == Qt.MidButton:
			tab = self.tabBar().tabAt( event.pos() )
			if tab != self.pressedAt:
				self.pressedAt = -1
				return
			self.emit(SIGNAL('middleClicked(int)'), tab)

	def wheelEvent(self, event):
		if not self.tabBar().underMouse():
			return 
		degrees = event.delta() / 8
		steps = degrees / 15
		self.setCurrentIndex( ( self.currentIndex() + steps ) % self.count() )

class KooMainWindow(QMainWindow):
	
	def __init__(self):	
		QMainWindow.__init__(self)
		loadUi( common.uiPath( "mainwindow.ui" ), self ) 
		self.showMaximized()	

		self.fixedWindowTitle = self.windowTitle()

		self.uiServerInformation.setText( _('Press Ctrl+O to login') )

		self.tabWidget = MainTabWidget( self. centralWidget() )
		self.connect( self.tabWidget, SIGNAL("currentChanged(int)"), self.currentChanged )
		self.connect( self.tabWidget, SIGNAL("middleClicked(int)"), self.closeTab )

		self.pushClose = QToolButton( self.tabWidget )
		self.pushClose.setIcon( QIcon( ':/images/images/close_tab.png' ) )
		self.pushClose.setAutoRaise( True )
		self.pushClose.setSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed )
		self.pushClose.setToolTip( _('Close tab') )
		self.connect(self.pushClose, SIGNAL('clicked()'), self.closeCurrentTab )

		self.tabWidget.setCornerWidget( self.pushClose, Qt.TopRightCorner )

		self.layout = self.centralWidget().layout()
		self.layout.setSpacing( 2 )
		self.layout.addWidget( self.tabWidget )
		self.layout.addWidget( self.frame )	
		
		self.connect( self.actionClose, SIGNAL("triggered()"), self.closeCurrentTab )
		self.connect( self.actionConnect ,SIGNAL("triggered()"), self.showLoginDialog )
		self.connect( self.actionDisconnect ,SIGNAL("triggered()"), self.logout )
		self.connect( self.actionSendRequest, SIGNAL("triggered()"), self.newRequest )
		self.connect( self.actionReadMyRequest, SIGNAL("triggered()"), self.pendingRequests )
		self.connect( self.actionWaitingRequests, SIGNAL("triggered()"), self.waitingRequests )
		self.connect( self.actionNewDatabase, SIGNAL("triggered()"), self.createDatabase )
		self.connect( self.actionExit, SIGNAL("triggered()"), self.close )
		self.connect( self.actionFullTextSearch, SIGNAL("triggered()"), self.fullTextSearch )
		self.connect( self.actionNextTab, SIGNAL("triggered()"), self.nextTab )
		self.connect( self.actionPreviousTab, SIGNAL("triggered()"), self.previousTab )
		self.connect( self.actionBackupDatabase, SIGNAL('triggered()'), self.backupDatabase )
		self.connect( self.actionRestoreDatabase, SIGNAL('triggered()'), self.restoreDatabase )
		self.connect( self.actionDropDatabase, SIGNAL('triggered()'), self.dropDatabase )
		self.connect( self.actionAdminPassword, SIGNAL('triggered()'), self.changeAdministratorPassword )
		self.connect( self.actionPreferences, SIGNAL('triggered()'), self.userPreferences )
		self.connect( self.actionOpenMenuTab, SIGNAL('triggered()'), self.openMenuTab )
		self.connect( self.actionOpenHomeTab, SIGNAL('triggered()'), self.openHomeTab )
		self.connect( self.actionClearCache, SIGNAL('triggered()'), self.clearCache )

		self.connect( self.actionSupportRequest, SIGNAL('triggered()'), self.supportRequest )
		self.connect( self.actionKooManual, SIGNAL('triggered()'), self.kooManual )
		self.connect( self.actionOpenErpManual, SIGNAL('triggered()'), self.openErpManual )
		self.connect( self.actionTips, SIGNAL('triggered()'), self.showTipOfTheDay )
		self.connect( self.actionContextualHelp, SIGNAL('triggered()'), self.contextHelp )
		self.connect( self.actionShortcuts, SIGNAL('triggered()'), self.showShortcuts )
		self.connect( self.actionLicense, SIGNAL('triggered()'), self.showLicense )
		self.connect( self.actionAbout, SIGNAL('triggered()'), self.showAboutDialog )
		
		self.connect( self.actionFormDesigner, SIGNAL('triggered()'), self.formDesigner )

		# Connect request buttons
		self.connect( self.pushReadRequests, SIGNAL('clicked()'), self.pendingRequests )
		self.connect( self.pushSendRequest, SIGNAL('clicked()'), self.newRequest )

		# These actions are not handled by the Main Window but by the currently opened tab.
		# What we do here, is connect all these actions to a single handler that will
		# call the current child/tab/form. This is handled this way instead of signals because we
		# may have several windows opened at the same time and all children would receive
		# the signal...
		self.actions = [ 'New', 'Save', 'Delete', 'Find', 'Previous', 'Next', 'Open', 
			'Reload', 'Switch', 'Attach', 'Export', 'Import', 'GoToResourceId', 'Plugins',
			'Duplicate', 'AccessLog' ]
		for x in self.actions:
			action = eval('self.action'+ x)
			self.connect( action, SIGNAL( 'triggered()' ), self.callChildView )

		self.updateEnabledActions()

		# Stores the id of the menu action. This is to avoid opening two menus
		# when 'action_id' returns the same as 'menu_id'
		self.menuId = False
		self.requestsTimer = QTimer()
		self.connect( self.requestsTimer, SIGNAL('timeout()'), self.updateRequestsStatus )
		self.pendingRequests = -1 

		# System Tray
		self.actionOpenPartnersTab = QAction( self )
		self.actionOpenPartnersTab.setIcon( QIcon( ':/images/images/partner.png' ) )
		self.actionOpenPartnersTab.setText( _('Open partners tab') )
		self.connect( self.actionOpenPartnersTab, SIGNAL('triggered()'), self.openPartnersTab )

		self.actionOpenProductsTab = QAction( self )
		self.actionOpenProductsTab.setIcon( QIcon( ':/images/images/product.png' ) )
		self.actionOpenProductsTab.setText( _('Open products tab') )
		self.connect( self.actionOpenProductsTab, SIGNAL('triggered()'), self.openProductsTab )
		
		self.systemTrayMenu = QMenu()
		self.systemTrayMenu.addAction( self.actionFullTextSearch )
		self.systemTrayMenu.addAction( self.actionOpenPartnersTab ) 
		self.systemTrayMenu.addAction( self.actionOpenProductsTab ) 
		self.systemTrayMenu.addAction( self.actionOpenMenuTab )
		self.systemTrayMenu.addSeparator()
		self.systemTrayMenu.addAction( self.actionSendRequest )
		self.systemTrayMenu.addAction( self.actionReadMyRequest )
		self.systemTrayMenu.addAction( self.actionWaitingRequests )
		self.systemTrayMenu.addSeparator()
		self.systemTrayMenu.addAction( self.actionExit )

		self.systemTrayIcon = QSystemTrayIcon( self )
		self.systemTrayIcon.setIcon( QIcon(":/images/images/tinyerp-icon-32x32.png") )
		self.systemTrayIcon.setContextMenu( self.systemTrayMenu )
		self.connect( self.systemTrayIcon, SIGNAL('activated(QSystemTrayIcon::ActivationReason)'), self.systemTrayIconActivated )

	def systemTrayIconActivated(self, reason):
		if reason != QSystemTrayIcon.DoubleClick:
			return
		self.setVisible( not self.isVisible() )
		if self.isMinimized():
			self.showNormal()

	def openPartnersTab(self):
		api.instance.createWindow(None, 'res.partner', mode='tree')
		if not self.isVisible():
			self.showNormal()

	def openProductsTab(self):
		api.instance.createWindow(None, 'product.product', mode='tree')
		if not self.isVisible():
			self.showNormal()

	def startRequestsTimer(self):
		# Every X minutes check for new requests and put the number of open
		# requests in the appropiate space in the status bar
		self.requestsTimer.start( options.options.get( 'requests_refresh_interval', 5 * 60 ) * 1000 )
		
	def formDesigner(self):
		dialog = FormDesigner(self)
		dialog.show()

	## @brief Closes the given tab smartly.
	#
	# First asks the widget in the tab if it can be closed and if so, it removes it.
	# Note that the widget might ask the user some questions, for example when there's
	# modified data in a form.
	# It returns True if all tabs could be closed, False otherwise. If there are no 
	# tabs always returns True.
	def closeTab(self, tab):
		wid = self.tabWidget.widget(tab)
		if wid:
			# Ask the current tab if it can be closed
			if not wid.canClose():
				return False
		self.tabWidget.removeTab( tab ) 
		del wid
		self.updateEnabledActions()
		return True
		
	## @brief Closes the current tab smartly. 
	def closeCurrentTab(self):
		return self.closeTab( self.tabWidget.currentIndex() )

	def fullTextSearch(self):
		# Ensure the window is shown as it might be called from the system tray icon
		# If we don't do this the dialog is shown, but when it's closed the whole
		# application is closed too.
		if not self.isVisible():
			self.showNormal()

		win = win_full_text_search.FullTextSearchDialog(self)
		if win.exec_() == QDialog.Rejected:
			return
		self.setCursor( Qt.WaitCursor )
		res = win.result
		api.instance.createWindow(None, res[1], res[0], view_type='form', mode='form,tree')
		self.unsetCursor()

	def nextTab(self):
		pn = self.tabWidget.currentIndex()
		if pn == self.tabWidget.count() - 1:
			pn = 0
		else:
			pn = pn + 1
		self.tabWidget.setCurrentIndex( pn )

	def previousTab(self):
		pn = self.tabWidget.currentIndex()
		if pn == 0:
			pn = self.tabWidget.count() - 1
		else:
			pn = pn - 1
		self.tabWidget.setCurrentIndex( pn )

	def userPreferences(self):
		actions = rpc.session.execute('/object', 'execute', 'ir.values', 'get', 'meta', False, [('res.users',False)], True, rpc.session.context, True)
		win = win_preference.win_preference('res.users', rpc.session.uid, actions, self)
		if win.exec_() == QDialog.Rejected:
			return
		rpc.session.reloadContext()

	def newRequest(self):
		api.instance.createWindow(None, 'res.request', False, 
			[('act_from','=',rpc.session.uid)], 'form', mode='form,tree')

	## Opens a new tab with requests pending for the user to resolve
	def pendingRequests(self):
		api.instance.createWindow(False, 'res.request', False, 
			[('act_to','=',rpc.session.uid)], 'form', mode='tree,form')

	## Opens a new tab with all unsolved requests posted by the user
	def waitingRequests(self):
		api.instance.createWindow(False, 'res.request', False, 
			[('act_from','=',rpc.session.uid), ('state','=','waiting')], 'form', mode='tree,form')

	## Updates the status bar with the number of pending requests.
	#
	#  Note that this function uses rpc.session.call() so exceptions are ignored, because this
	#  function is called every five minutes. We don't want any temporary disconnection of the
	#  server to annoy the user unnecessarily.
	def updateRequestsStatus(self):
		# We use 'try' because we might not have logged in or the server might
		# be down temporarily. This way the user isn't notified unnecessarily.
		try:
			uid = rpc.session.uid
			ids,ids2 = rpc.session.call('/object', 'execute', 'res.request', 'request_get')
			if len(ids):
				message = _('%s request(s)') % len(ids)
			else:
				message = _('No request')
			if len(ids2):
				message += _(' - %s pending request(s)') % len(ids2)
			self.uiRequests.setText( message )
			self.systemTrayIcon.setToolTip( message )
			if self.pendingRequests != -1 and self.pendingRequests < len(ids):
				QApplication.alert( self )
				if self.systemTrayIcon.isVisible() and not self.isVisible():
					self.systemTrayIcon.showMessage( _("New Request"), _("You've received a new request") )
			self.pendingRequests = len(ids)
			return (ids, ids2)
		except:
			return ([], [])

	def showLoginDialog(self):
		LoginDialog.defaultHost = options.options['login.server']
		LoginDialog.defaultPort = options.options['login.port']
		LoginDialog.defaultProtocol = options.options['login.protocol']
		LoginDialog.defaultUserName = options.options['login.login']
		dialog = LoginDialog( self )
		while dialog.exec_() == QDialog.Accepted:
			self.login( dialog.url, dialog.databaseName )
			if rpc.session.open:
				return

	## Logs into the specified database and server.
	#
	# If correctly logged in, the parameters are stored as the default
	# config for the next time. Note that the function first will check
	# if it can close all opened tabs. If the user permits so by storing
	# or discarding all modified tabs, then it logs in. If no tabs are
	# opened or non of them have been modified, then no questions are asked.
	# @param url string describing the server
	# @param databaseName name of the database to log into
	def login(self, url, databaseName):
		# Before connecting to the specified database
		# we check each of the tabs for changes. If the user
		# cancels in any of them we won't connect.
		if not self.closeAllTabs():
			return

		try:
			log_response = rpc.session.login(url, databaseName)
			url = QUrl( url )
			if log_response==rpc.session.LoggedIn:
				options.options.loadSettings()

				iconVisible = options.options.get( 'show_system_tray_icon', True )
				self.systemTrayIcon.setVisible( iconVisible )

				# Start timer once settings have been loaded because
				# the request interval can be configured
				self.startRequestsTimer()
				options.options['login.server'] = unicode( url.host() )
				options.options['login.login'] = unicode( url.userName() )
				options.options['login.port'] = url.port()
				options.options['login.protocol'] = unicode( url.scheme() ) + '://'
				options.options['login.db'] = databaseName
				options.options.save()
			        self.openMenuTab()
				self.openHomeTab()

				self.updateRequestsStatus()
			elif log_response==rpc.session.Exception:
				QMessageBox.warning(self, _('Connection error !'), _('Unable to connect to the server !')) 
			elif log_response==rpc.session.InvalidCredentials:
				QMessageBox.warning(self, _('Connection error !'), _('Bad username or password !'))

		except rpc.RpcException, e:
			(e1,e2) = e
			common.error(_('Connection Error !'),e1,e2)
			rpc.session.logout()

	## Closes all tabs smartly, that is using closeCurrentTab()
	def closeAllTabs(self):
		while self.tabWidget.count() > 0:
			if not self.closeCurrentTab():
				return False
		return True

	def logout(self):
		if not self.closeAllTabs():
			return
		self.uiRequests.clear()
		self.uiUserName.setText( _('Not logged !') )
		self.uiServerInformation.setText( _('Press Ctrl+O to login') )
		self.setWindowTitle( self.fixedWindowTitle )
		self.updateEnabledActions()
		rpc.session.logout()
		
	def supportRequest(self):
		common.support()

	def kooManual(self):
		dir = os.path.abspath(os.path.dirname(__file__))
		index = dir + '/../../../doc/html/index.html'
		if os.path.exists( index ):
			QDesktopServices.openUrl( QUrl( index ) )
		else:
			QDesktopServices.openUrl( QUrl('http://www.nan-tic.com/ftp/ktiny-doc/index.html') )

	def openErpManual(self):
		QDesktopServices.openUrl( QUrl('http://tinyerp.com/documentation/user-manual/') )

	def contextHelp(self):
		model = self.tabWidget.currentWidget().model
		l = rpc.session.context.get('lang','en')
		url = 'http://tinyerp.org/scripts/context_index.php?model=%s&lang=%s' % (model,l)
		QDesktopServices.openUrl( QUrl(url) )

	def showTipOfTheDay(self):
		dialog = common.TipOfTheDayDialog(self)
		dialog.exec_()
		
	def showLicense(self):
		dialog = QDialog( self )
		loadUi( common.uiPath('license.ui'), dialog )
		dialog.exec_()

	def showAboutDialog(self):
		dialog = QDialog( self )
		loadUi( common.uiPath('about.ui'), dialog )
		dialog.uiTiny.setHtml( unicode(dialog.uiTiny.toHtml()) % '1.0.0' )
		dialog.exec_()

	def showShortcuts(self):
		dialog = QDialog( self )
		loadUi( common.uiPath('shortcuts.ui'), dialog )
		dialog.exec_()


	## @brief Opens the Menu Tab.
	#
	# If a tab menu already exists it's risen, otherwise a new one is created
	# and rised.
	def openMenuTab(self):

		# Ensure the window is shown as it might be called from the system tray icon
		if not self.isVisible():
			self.showNormal()

		# Search if a menu tab already exists and rise it
		for p in range(self.tabWidget.count()):
			if self.tabWidget.widget(p).model=='ir.ui.menu':
				self.tabWidget.setCurrentIndex(p)
				return 

		# If no menu tab exists query the server and open it
		id = rpc.session.execute('/object', 'execute', 'res.users', 'read', [rpc.session.uid], [ 'menu_id','name'], rpc.session.context)
		self.uiUserName.setText( id[0]['name'] or '' )
		self.uiServerInformation.setText( "%s [%s]" % (rpc.session.url, rpc.session.databaseName) )
		self.setWindowTitle( self.fixedWindowTitle + " - [%s]" % rpc.session.databaseName )

		# Store the menuId so we ensure we don't open the menu twice when
		# calling openHomeTab()
		self.menuId = id[0]['menu_id'][0]

 		if not id[0]['menu_id']:
			QMessageBox.warning(self, _('Access denied'), _('You can not log into the system !\nAsk the administrator to verify\nyou have an action defined for your user.') )
 			rpc.session.logout()
			return 

		api.instance.execute(self.menuId, {'window':self })


	## @brief Opens Home Tab.
	#
	# Home tab is an action specified in the server which usually is a 
	# dashboard, but could be anything.
	def openHomeTab(self):
		id = rpc.session.execute('/object', 'execute', 'res.users', 'read', [rpc.session.uid], [ 'action_id','name'], rpc.session.context)

 		if not id[0]['action_id']:
			return 
		id = id[0]['action_id'][0]
		if not id:
			return

		# Do not open the action if the id is the same as the menu id.
		if id == self.menuId:
			return
		api.instance.execute(id, {'window':self })

	def clearCache(self):
		viewsettings.ViewSettings.clear()
		if rpc.session.cache:
			rpc.session.cache.clear()

	def closeEvent(self, event):
		if QMessageBox.question(self, _("Quit"), _("Do you really want to quit ?"), _("Yes"), _("No")) == 1:
			event.ignore()	
		wid = self.tabWidget.currentWidget()
		if wid:
			# Ask the current tab if it can be closed
			if not wid.canClose():
				event.ignore()

	def addWindow(self, win):
		self.tabWidget.addTab( win, win.name )
		self.tabWidget.setCurrentIndex( self.tabWidget.count()-1 )

	def updateEnabledActions(self):
		view = self.tabWidget.currentWidget()
		for x in self.actions:
			action = eval( 'self.action' + x )
			if view and x in view.handlers:
				action.setEnabled( True )
			else:
				action.setEnabled( False )

		if rpc.session.open:
			self.actionFullTextSearch.setEnabled( True )
		else:
			self.actionFullTextSearch.setEnabled( False )

		# Update the 'Reports', 'Actions' and 'Browse' Menu entries
		self.menuReports.clear()
		self.menuBrowse.clear()
		self.menuActions.clear()
		reports = False
		browse = False
		actions = False
		if view and view.actions():
			for x in view.actions():
				if x.type() == 'print':
					self.menuReports.addAction( x )
					reports = True
				elif x.type() == 'relate':
					self.menuBrowse.addAction( x )
					browse = True
				else:
					self.menuActions.addAction( x )	
					actions = True
			
		self.menuReports.setEnabled( reports )
		self.menuBrowse.setEnabled( browse )
		self.menuActions.setEnabled( actions )

	def callChildView( self ):
		o = self.sender()
		action = str( o.objectName() ).replace('action','')
		wid = self.tabWidget.currentWidget()
		if wid:
			res = True
			if action in wid.handlers:
				res = wid.handlers[action]()

	def currentChanged( self, page ): 
		self.updateEnabledActions()

	def createDatabase(self):
		result = {}
		dialog = DatabaseCreationDialog(self)
		ret = dialog.exec_()
		if ret == QDialog.Accepted:
			self.login( dialog.url, dialog.databaseName )

	def dropDatabase(self):
		dialog = DatabaseDialog( DatabaseDialog.TypeSelect, _('Delete a database'), self )
		r = dialog.exec_()

		if r == QDialog.Rejected:
			return
		try:
			self.setCursor( Qt.WaitCursor )
			rpc.database.execute(dialog.url, 'drop', dialog.password, dialog.databaseName )
			self.unsetCursor()
			QMessageBox.information( self, _('Database removal'), _('Database dropped successfully!') )
		except Exception, e:
			self.unsetCursor()
			if e.faultString=='AccessDenied:None':
				QMessageBox.warning( self, _("Could not drop database."), _('Bad database administrator password !') )
			else:
				QMessageBox.warning( self, _("Database removal"), _("Couldn't drop database") )

	def restoreDatabase(self):
		fileName = QFileDialog.getOpenFileName(self, 'Open backup file...')
		if fileName.isNull():
			return
		dialog = DatabaseDialog( DatabaseDialog.TypeEdit, _('Delete a database'), self )
		r = dialog.exec_()
		if r == QDialog.Rejected:
			return
		try:
			self.setCursor( Qt.WaitCursor )
			f = file(fileName, 'rb')
			data = base64.encodestring(f.read())
			f.close()
			rpc.database.execute(dialog.url, 'restore', dialog.password, dialog.databaseName, data)
			self.unsetCursor()
			QMessageBox.information( self, '', _('Database restored successfully!') )
		except Exception,e:
			self.unsetCursor()
			if e.faultString=='AccessDenied:None':
				QMessageBox.warning(self, _('Could not restore database'), _('Bad database administrator password!') )
			else:
				QMessageBox.warning(self, _('Could not restore database'), _('There was an error restoring the database!') )

	def backupDatabase(self):
		dialog = DatabaseDialog( DatabaseDialog.TypeSelect, _('Backup a database'), self )
		r = dialog.exec_()
		if r == QDialog.Rejected:
			return
		fileName = QFileDialog.getSaveFileName(self, 'Save as...')
		if fileName.isNull():
			return
		try:
			self.setCursor( Qt.WaitCursor )
			dump_b64 = rpc.database.execute(dialog.url, 'dump', dialog.password, dialog.databaseName)
			dump = base64.decodestring(dump_b64)
			f = file(fileName, 'wb')
			f.write(dump)
			f.close()
			self.unsetCursor()
			QMessageBox.information( self, '', _("Database backuped successfully!"))
		except Exception, e:
			self.unsetCursor()
			QMessageBox.warning( self, '', _('Could not backup database.\n%s') % (str(e)) )

	def changeAdministratorPassword(self):
		dialog = AdministratorPasswordDialog( self )
		dialog.exec_()

