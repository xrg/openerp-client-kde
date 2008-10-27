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
from PyQt4.uic import *
#import options
from Common import Common
import ServerConfigurationDialog

class LoginDialog( QDialog ):
	defaultHost = ''
	defaultPort = 0
	defaultProtocol = ''
	defaultUserName = ''

	def __init__(self, parent=None ):
		QDialog.__init__(self, parent)
		loadUi( Common.uiPath('login.ui'), self ) 
		self.databaseName = ''
		self.connect(self.pushCancel,SIGNAL("clicked()"),self.slotCancel )
		self.connect(self.pushAccept,SIGNAL("clicked()"),self.slotAccept )
		self.connect(self.pushChange,SIGNAL("clicked()"),self.slotChange )
		self.init()
	
	def setDatabaseName( self, name ):
		self.databaseName = name

	def init(self):
		uid = 0
		self.uiNoConnection.hide()
		#host = Options.options['login.server']
		#port = Options.options['login.port']
		#protocol = Options.options['login.protocol']
		host = LoginDialog.defaultHost
		port = LoginDialog.defaultPort
		protocol = LoginDialog.defaultProtocol
		url = '%s%s:%s' % (protocol, host, port)
		self.uiServer.setText( url )
		#self.uiUserName.setText( Options.options['login.login'] )
		self.uiUserName.setText( LoginDialog.defaultUserName )
		res = self.refreshList()

	def refreshList(self):
		res = ServerConfigurationDialog.refreshDatabaseList(self.uiDatabase, str( self.uiServer.text() ), self.databaseName )
		print res
		if res == -1:
			self.uiNoConnection.setText('<b>'+_('Could not connect to server !')+'</b>')
			self.uiNoConnection.show()
			self.uiDatabase.hide()
			self.pushAccept.setEnabled(False)
		elif res==0:
			self.uiNoConnection.setText('<b>'+_('No database found, you must create one !')+'</b>')
			self.uiNoConnection.show()
			self.uiDatabase.hide()
			self.pushAccept.setEnabled(False)
		else:
			self.uiNoConnection.hide()
			self.uiDatabase.show()
			self.pushAccept.setEnabled(True)
		return res

	def slotChange(self):
		dialog = ServerConfigurationDialog.ServerConfigurationDialog( self )
		dialog.setDefault( str( self.uiServer.text() ) )
		dialog.exec_()
		QApplication.setOverrideCursor( Qt.WaitCursor )
		self.uiServer.setText( dialog.url )
		self.refreshList()
		QApplication.restoreOverrideCursor()

	def slotAccept( self ):
		m = QUrl( self.uiServer.text() )
		m.setUserName( self.uiUserName.text() )
		m.setPassword( self.uiPassword.text() )
		if m.isValid():	
			self.url = unicode( m.toString() )
			self.databaseName = unicode( self.uiDatabase.currentText() )
			self.accept()
		else:
			self.reject()

	def slotCancel(self):
		self.reject()

