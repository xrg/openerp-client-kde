#!/usr/bin/python
#############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#					Fabien Pinckaers <fp@tiny.Be>
#					Angel Alvarez <angel_alse@yahoo.es>
#
# $Id: main.py 4778 2006-12-05 14:15:56Z ced $
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

import service
import options

from window import windowservice, win_preference, win_full_text_search
from createdb import CreateDatabaseDialog
from choosedb import ChooseDatabaseDialog
from formdesigner import FormDesigner
import re
import base64

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import * 

from askserver import *
from login import * 
from adminpwd import *
from common import common

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

class MainWindow(QMainWindow):
	
	def __init__(self):	
		QMainWindow.__init__(self)
		QResource.registerResource( common.uiPath( "common.rcc" ) )
		loadUi( common.uiPath( "mainwindow.ui" ), self ) 
		self.showMaximized()	

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
		
		#TODO: Make shortcuts configurable
		self.actionConnect.setShortcut("Ctrl+O")
		self.actionFind.setShortcut("Ctrl+F")
		self.actionNew.setShortcut("Ctrl+N")
		self.actionSave.setShortcut("Ctrl+S")
		self.actionDelete.setShortcut("Ctrl+D")
		self.actionSwitch.setShortcut("Ctrl+L")
		self.actionClose.setShortcut("Ctrl+W")
		self.actionPreviousTab.setShortcut("Ctrl+PgUp")
		self.actionNextTab.setShortcut("Ctrl+PgDown")
		self.actionFullTextSearch.setShortcut("Ctrl+T")
		self.actionReload.setShortcut("F5")
		self.actionDuplicate.setShortcut("Ctrl+Shift+D")
		self.actionPrevious.setShortcut("Alt+PgUp")
		self.actionNext.setShortcut("Alt+PgDown")

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

		self.connect( self.actionSupportRequest, SIGNAL('triggered()'), self.supportRequest )
		self.connect( self.actionKTinyManual, SIGNAL('triggered()'), self.kTinyManual )
		self.connect( self.actionTinyErpManual, SIGNAL('triggered()'), self.tinyErpManual )
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

		spool = service.LocalService('spool')
		spool.subscribe('gui.window', self.win_add )

		# Stores the id of the menu action. This is to avoid opening two menus
		# when 'action_id' returns the same as 'menu_id'
		self.menuId = False

		# Every 5 minutes check for new requests and put the number of open
		# requests in the appropiate space in the status bar
		self.requestsTimer = QTimer()
		self.connect( self.requestsTimer, SIGNAL('timeout()'), self.updateRequestsStatus )
		self.requestsTimer.start( 5 * 60 * 1000 )

	def formDesigner(self):
		dialog = FormDesigner(self)
		dialog.show()

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
		
	## Closes the current tab smartly. 
	#
	# First asks the widget in the tab if it can be closed and if so, it removes it.
	# Note that the widget might ask the user some questions, for example when there's
	# modified data in a form.
	# It returns True if all tabs could be closed, False otherwise. If there are no 
	# tabs always returns True.
	def closeCurrentTab(self):
		return self.closeTab( self.tabWidget.currentIndex() )
		#wid = self.tabWidget.currentWidget()
		#if wid:
			## Ask the current tab if it can be closed
			#if not wid.canClose():
				#return False
		#self.tabWidget.removeTab( self.tabWidget.currentIndex() ) 
		#del wid
		#self.updateEnabledActions()
		#return True

	def fullTextSearch(self):
		win = win_full_text_search.FullTextSearchDialog(self)
		if win.exec_() == QDialog.Rejected:
			return
		self.setCursor( Qt.WaitCursor )
		res = win.result
		obj = service.LocalService('gui.window')
		obj.create(None, res[1], res[0], view_type='form', mode='form,tree')
		self.setCursor( Qt.ArrowCursor )

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
		obj = service.LocalService('gui.window')
		obj.create(None, 'res.request', False, [('act_from','=',rpc.session.uid)], 'form', mode='form,tree')

	## Opens a new tab with requests pending for the user to resolve
	def pendingRequests(self):
		ids, ids2 = self.updateRequestsStatus()
		obj = service.LocalService('gui.window')
		obj.create(False, 'res.request', ids, [('act_to','=',rpc.session.uid)], 'form', mode='tree,form')

	## Opens a new tab with all unsolved requests posted by the user
	def waitingRequests(self):
		ids, ids2 = self.updateRequestsStatus()
		obj = service.LocalService('gui.window')
		obj.create(False, 'res.request', ids, [('act_from','=',rpc.session.uid), ('state','=','waiting')], 'form', mode='tree,form')

	## Updates the status bar with the number of pending requests.
	#
	#  Note that this function uses rpc.session.call() so exceptions are ignored, because this
	#  function is called every five minutes. We don't want any temporary disconnection of the
	#  server to annoy the user unnecessarily.
	def updateRequestsStatus(self):
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
			return (ids, ids2)
		except:
			return ([], [])

	def showLoginDialog(self):
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
			if log_response==1:
				options.options['login.server'] = unicode( url.host() )
				options.options['login.login'] = unicode( url.userName() )
				options.options['login.port'] = url.port()
				options.options['login.protocol'] = unicode( url.scheme() ) + '://'
				options.options['login.db'] = databaseName
				options.options.save()
			        self.openMenuTab()
				self.openHomeTab()

				self.updateRequestsStatus()
			elif log_response==-1:
				QMessageBox.warning(self, _('Connection error !'), _('Unable to connect to the server !')) 
			elif log_response==-2:
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
		self.updateEnabledActions()
		rpc.session.logout()
		
	def supportRequest(self):
		common.support()

	def kTinyManual(self):
		dir = os.path.abspath(os.path.dirname(__file__))
		index = dir + '/../../../doc/html/index.html'
		if os.path.exists( index ):
			QDesktopServices.openUrl( QUrl( index ) )
		else:
			QDesktopServices.openUrl( QUrl('http://www.nan-tic.com/ftp/ktiny-doc/index.html') )

	def tinyErpManual(self):
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
		dialog.uiTiny.setHtml( str(dialog.uiTiny.toHtml()) % tinyerp_version )
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
		# Search if a menu tab already exists and rise it
		for p in range(self.tabWidget.count()):
			if self.tabWidget.widget(p).model=='ir.ui.menu':
				self.tabWidget.setCurrentIndex(p)
				return 

		# If no menu tab exists query the server and open it
		id = rpc.session.execute('/object', 'execute', 'res.users', 'read', [rpc.session.uid], [ 'menu_id','name'], rpc.session.context)
		self.uiUserName.setText( id[0]['name'] or '' )
		self.uiServerInformation.setText( "%s [%s]" % (rpc.session.url, rpc.session.databaseName) )

 		if not id[0]['menu_id']:
			QMessageBox.warning(self, _('Access denied'), _('You can not log into the system !\nAsk the administrator to verify\nyou have an action defined for your user.') )
 			rpc.session.logout()
			return 
		
		# Store the menuId so we ensure we don't open the menu twice when
		# calling openHomeTab()
		self.menuId = id[0]['menu_id'][0]


		obj = service.LocalService('action.main')
		win = obj.execute(self.menuId, {'window':self })

	## @brief Opens the Home Tab.
	#
	# The home tab is an action specified in the server which usually is a 
	# dashboard, but could be anything.
	def openHomeTab(self):
		id = rpc.session.execute('/object', 'execute', 'res.users', 'read', [rpc.session.uid], [ 'action_id','name'], rpc.session.context)

 		if not id[0]['action_id']:
			return 
		id = id[0]['action_id'][0]

		# Do not open the action if the id is the same as the menu id.
		if id == self.menuId:
			return
		obj = service.LocalService('action.main')
		obj.execute(id, {'window':self })

	def closeEvent(self, event):
		if QMessageBox.question(self, _("Quit"), _("Do you really want to quit ?"), _("Yes"), _("No")) == 1:
			event.ignore()	
		wid = self.tabWidget.currentWidget()
		if wid:
			# Ask the current tab if it can be closed
			if not wid.canClose():
				event.ignore()

	def win_add(self, win, datas):
		self.tabWidget.addTab( win, win.name )
		self.tabWidget.setCurrentIndex( self.tabWidget.count()-1 )

	def updateEnabledActions(self):
		view = self.tabWidget.currentWidget()
		#try:
		for x in self.actions:
			action = eval( 'self.action' + x )
			if view and x in view.handlers:
				action.setEnabled( True )
			else:
				action.setEnabled( False )
		#except:
		#	for x in self.actions:
		#		action = eval( 'self.action' + x )
		#		action.setEnabled( False )

		if rpc.session.open:
			self.actionFullTextSearch.setEnabled( True )
		else:
			self.actionFullTextSearch.setEnabled( False )

		# Update the 'Actions' Menu entry
		if view:
			self.menuActions.clear()
			last = None
			if view.actions():
				for x in view.actions():
					if last and last != x.type():
						self.menuActions.addSeparator()
					last = x.type()
					self.menuActions.addAction( x )	
				self.menuActions.setEnabled( True )
			else:
				self.menuActions.setEnabled( False )
		else:
			self.menuActions.setEnabled( False )

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
		dialog = CreateDatabaseDialog(self)
		ret = dialog.exec_()
		if ret == QDialog.Accepted:
			self.login( dialog.url, dialog.databaseName )

	def dropDatabase(self):
		dialog = ChooseDatabaseDialog( ChooseDatabaseDialog.TypeSelect, _('Delete a database'), self )
		r = dialog.exec_()

		if r == QDialog.Rejected:
			return
		try:
			self.setCursor( Qt.WaitCursor )
			rpc.database.execute(dialog.url, 'drop', dialog.password, dialog.databaseName )
			self.setCursor( Qt.ArrowCursor )
			QMessageBox.information( self, _('Database removal'), _('Database dropped successfully!') )
		except Exception, e:
			self.setCursor( Qt.ArrowCursor )
			if e.faultString=='AccessDenied:None':
				QMessageBox.warning( self, _("Could not drop database."), _('Bad database administrator password !') )
			else:
				QMessageBox.warning( self, _("Database removal"), _("Couldn't drop database") )

	def restoreDatabase(self):
		fileName = QFileDialog.getOpenFileName(self, 'Open backup file...')
		if fileName.isNull():
			return
		dialog = ChooseDatabaseDialog( ChooseDatabaseDialog.TypeEdit, _('Delete a database'), self )
		r = dialog.exec_()
		if r == QDialog.Rejected:
			return
		try:
			self.setCursor( Qt.WaitCursor )
			f = file(fileName, 'rb')
			data = base64.encodestring(f.read())
			f.close()
			rpc.database.execute(dialog.url, 'restore', dialog.password, dialog.databaseName, data)
			self.setCursor( Qt.ArrowCursor )
			QMessageBox.information( self, '', _('Database restored successfully!') )
		except Exception,e:
			self.setCursor( Qt.ArrowCursor )
			if e.faultString=='AccessDenied:None':
				QMessageBox.warning(self, _('Could not resotre database'), _('Bad database administrator password!') )
			else:
				QMessageBox.warning(self, _('Could not restore database'))

	def backupDatabase(self):
		dialog = ChooseDatabaseDialog( ChooseDatabaseDialog.TypeSelect, _('Backup a database'), self )
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
			self.setCursor( Qt.ArrowCursor )
			QMessageBox.information( self, '', _("Database backuped successfully!"))
		except Exception, e:
			self.setCursor( Qt.ArrowCursor )
			QMessageBox.warning( self, '', _('Could not backup database.\n%s') % (str(e)) )

	def changeAdministratorPassword(self):
		dialog = ChangeAdministratorPassword( self )
		dialog.exec_()

