##############################################################################
#
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

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from Common.Ui import *
from Koo.Common import Common
from Koo.Common import Url
from DatabaseDialog import *
import ServerConfigurationDialog
from DatabaseCreationDialog import DatabaseCreationDialog

(LoginDialogUi, LoginDialogBase) = loadUiType( Common.uiPath('login.ui') )

## @brief The LoginDialog class shows a Dialog for logging into OpenObject server.
#
# The dialog will send the accept() signal if the user accepted or reject() if she
# cancelled it or didn't provide a valid server. If accept() was sent, two properties
# 'url' and 'databaseName' contain the information introduced by the user.
class LoginDialog( QDialog, LoginDialogUi ):
	defaultHost = ''
	defaultPort = 0
	defaultProtocol = ''
	defaultUserName = ''

	def __init__(self, parent=None ):
		QDialog.__init__(self, parent)
		LoginDialogUi.__init__(self)
		self.setupUi( self )

		self.pushCreateDatabase.hide()
		self.pushRestoreDatabase.hide()
		self.uiTextDatabase.hide()
		self.databaseName = ''

		QTimer.singleShot( 0, self.initGui )
	
	def setDatabaseName( self, name ):
		self.databaseName = name

	def initGui(self):
		self.connect( self.pushCancel, SIGNAL("clicked()"), self.slotCancel )
		self.connect( self.pushAccept, SIGNAL("clicked()"), self.slotAccept )
		self.connect( self.pushChange, SIGNAL("clicked()"), self.slotChange )
		self.connect( self.uiDatabase, SIGNAL('currentIndexChanged(int)'), self.checkWallet )
		self.connect( self.pushCreateDatabase, SIGNAL("clicked()"), self.createDatabase )
		self.connect( self.pushRestoreDatabase, SIGNAL("clicked()"), self.restoreDatabase )

		uid = 0
		self.uiNoConnection.hide()

		url = QUrl( Settings.value( 'login.url' ) )
		hasPassword = unicode( url.password() ) and True or False
		self.uiUserName.setText( url.userName() )
		url.setUserName( '' )
		self.uiPassword.setText( url.password() )
		url.setPassword( '' )
		self.uiServer.setText( url.toString() )
		res = self.refreshList()

	def refreshList(self):
		res = ServerConfigurationDialog.refreshDatabaseList(self.uiDatabase, str( self.uiServer.text() ), self.databaseName )
		if res == -1:
			self.uiNoConnection.setText('<b>'+_('Could not connect to server !')+'</b>')
			self.uiNoConnection.show()
			self.uiDatabase.hide()
			self.uiTextDatabase.hide()
			self.pushCreateDatabase.hide()
			self.pushRestoreDatabase.hide()
			self.pushAccept.setEnabled(False)
		elif res == 0:
			self.uiNoConnection.setText('<b>'+_('No database found, you must create one !')+'</b>')
			self.uiNoConnection.show()
			self.uiDatabase.hide()
			self.uiTextDatabase.hide()
			self.pushCreateDatabase.show()
			self.pushRestoreDatabase.show()
			self.pushAccept.setEnabled(False)
		else:
			self.uiNoConnection.hide()
			if res == -2:
				self.uiDatabase.hide()
				self.uiTextDatabase.show()
			else:
				self.uiDatabase.show()
				self.uiTextDatabase.hide()
			self.pushCreateDatabase.hide()
			self.pushRestoreDatabase.hide()
			self.pushAccept.setEnabled(True)

		try:
			Common.serverVersion = Rpc.database.call( str(self.uiServer.text()), 'server_version' )
			Common.serverMajorVersion = '.'.join( Common.serverVersion.split('.')[0] )
		except Rpc.RpcException:
			Common.serverVersion = None
			Common.serverMajorVersion= None

		return res

	def checkWallet(self):
		if Common.isKdeAvailable:
			from PyKDE4.kdeui import KWallet
			KWallet.Wallet.NetworkWallet()
			wallet = KWallet.Wallet.openWallet( KWallet.Wallet.NetworkWallet(), self.winId() )
			# If users presses 'Cancel' in KWallet's dialog it returns None
			if wallet:
				folder = '%s/%s' % (unicode(self.uiServer.text()), unicode(self.uiDatabase.currentText()))
				qtValues = wallet.readMap( folder )[1]
				values = {}
				for key, value in qtValues.iteritems():
					values[ unicode(key) ] = unicode( value )
				if 'username' in values:
					self.uiUserName.setText( values['username'] )
				if 'password' in values:
					self.uiPassword.setText( values['password'] )

	def slotChange(self):
		dialog = ServerConfigurationDialog.ServerConfigurationDialog( self )
		dialog.setUrl( Settings.value( 'login.url' ) )
		if dialog.exec_() == QDialog.Accepted:
			QApplication.setOverrideCursor( Qt.WaitCursor )
			self.uiServer.setText( dialog.url )
			self.refreshList()
			QApplication.restoreOverrideCursor()

	def slotAccept( self ):
		m = QUrl( self.uiServer.text() )
		m.setUserName( Url.encodeForUrl( self.uiUserName.text() ) )
		m.setPassword( Url.encodeForUrl( self.uiPassword.text() ) )
		if m.isValid():	
			self.url = unicode( m.toString() )
			if self.uiDatabase.isVisible():
				self.databaseName = unicode( self.uiDatabase.currentText() )
			else:
				self.databaseName = unicode( self.uiTextDatabase.text() )
			m.setPassword( '' )
			Settings.setValue( 'login.url', unicode( m.toString() ) )
			Settings.setValue( 'login.db', self.databaseName )
			Settings.saveToFile()
			self.accept()

			if Common.isKdeAvailable:
				storeWallet = Settings.value('kde.wallet','ask')
				if storeWallet == 'ask':
					answer = QMessageBox.question(self, 
						_('Wallet'), 
						_('Do you want to store your password in your wallet?'), 
						QMessageBox.Yes | QMessageBox.No | QMessageBox.YesToAll | QMessageBox.NoToAll
						)
					if answer == QMessageBox.YesToAll:
						Settings.setValue('kde.wallet', 'yes') 
						Settings.saveToFile()
						storeWallet = True
					elif answer == QMessageBox.NoToAll:
						Settings.setValue('kde.wallet', 'no')
						Settings.saveToFile()
						storeWallet = False
					elif answer == QMessageBox.Yes:
						storeWallet = True
					else:
						storeWallet = False

				if storeWallet:
					from PyKDE4.kdeui import KWallet
					KWallet.Wallet.NetworkWallet()
					wallet = KWallet.Wallet.openWallet( KWallet.Wallet.NetworkWallet(), self.winId() )
					folder = '%s/%s' % (unicode(self.uiServer.text()), self.databaseName)
					wallet.writeMap( folder, {
						'username': unicode( self.uiUserName.text() ),
						'password': unicode( self.uiPassword.text() ),
					})
		else:
			self.reject()

	def slotCancel(self):
		self.reject()

	def createDatabase(self):
		dialog = DatabaseCreationDialog(self)
		if dialog.exec_() == QDialog.Accepted:
			self.url = dialog.url
			self.databaseName = dialog.databaseName
			self.accept()

	def restoreDatabase(self):
		restoreDatabase( self )
		QApplication.setOverrideCursor( Qt.WaitCursor )
		self.refreshList()
		QApplication.restoreOverrideCursor()

