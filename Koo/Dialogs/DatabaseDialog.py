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
import ServerConfigurationDialog
from Koo.Common import Common
from Koo.Common import Options

(DatabaseDialogUi, DatabaseDialogBase) = loadUiType(  Common.uiPath('choosedb.ui') )

class DatabaseDialog( QDialog, DatabaseDialogUi ):
	# Database chooser type: 
	#  Select -> Shows a combo box for the database selection
	#  Edit   -> Shows a line edit for the database selection
	TypeSelect = 1
	TypeEdit   = 2

	def __init__(self, type, title, parent=None):
		QDialog.__init__(self, parent)
		DatabaseDialogUi.__init__(self)
		self.setupUi( self )

		self.type = type
		if type == DatabaseDialog.TypeSelect:
			self.uiDatabaseEditor.setVisible( False )
			self.uiDatabaseLabel.setBuddy( self.uiDatabaseSelector )
		else:
			self.uiDatabaseSelector.setVisible( False )
			self.uiDatabaseLabel.setBuddy( self.uiDatabaseEditor )

		host = Options.options['login.server']
		port = Options.options['login.port']
		secure = Options.options['login.secure']
		protocol = secure and 'https' or 'http'
		url = '%s://%s:%s' % (protocol, host, port)
		self.uiServer.setText( url )

		self.uiTitle.setText( title )
		self.setModal( True )
		self.uiInformation.setVisible( False )
		self.connect( self.pushChange, SIGNAL('clicked()'), self.slotChange )
		self.connect( self.pushAccept, SIGNAL('clicked()'), self.slotAccept )
		self.connect( self.pushCancel, SIGNAL('clicked()'), self.reject )
		self.refreshList()
	
	def refreshList(self):
		res = ServerConfigurationDialog.refreshDatabaseList(self.uiDatabaseSelector, str( self.uiServer.text() ) )
		if res == -1:
			self.uiInformation.setText('<b>'+_('Could not connect to server !')+'</b>')
			self.uiInformation.setVisible( True )
			self.uiDatabaseSelector.setEnabled( False )
			self.uiDatabaseEditor.setEnabled( False )
			self.pushAccept.setEnabled( False )
		elif res==0:
			self.uiInformation.setText('<b>'+_('No database found, you must create one !')+'</b>')
			self.uiInformation.setVisible( True )
			self.uiDatabaseSelector.setEnabled( False )
			self.uiDatabaseEditor.setEnabled( False )
			self.pushAccept.setEnabled( False )
		else:
			self.uiInformation.setVisible( False )
			self.uiDatabaseSelector.setEnabled( True )
			self.uiDatabaseEditor.setEnabled( True )
			self.pushAccept.setEnabled( True )
		return res
	
	def slotAccept(self):
		self.url = str( self.uiServer.text() )
		if self.type == DatabaseDialog.TypeSelect:
			self.databaseName = str( self.uiDatabaseSelector.currentText() )
		else:
			self.databaseName = str( self.uiDatabaseEditor.text() )
		self.password = str( self.uiPassword.text() )
		self.accept()
		
	def slotChange(self):
		dialog = ServerConfigurationDialog.ServerConfigurationDialog(self)
		dialog.setDefault( str( self.uiServer.text() ) )
		if dialog.exec_() == QDialog.Accepted:
			self.uiServer.setText( dialog.url )
			self.refreshList()

