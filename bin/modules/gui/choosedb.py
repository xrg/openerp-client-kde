from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *
import askserver
from common import common
from common import options

class ChooseDatabaseDialog( QDialog ):
	# Database chooser type: 
	#  Select -> Shows a combo box for the database selection
	#  Edit   -> Shows a line edit for the database selection
	TypeSelect = 1
	TypeEdit   = 2

	def __init__(self, type, title, parent=None):
		QDialog.__init__(self, parent)
		loadUi( common.uiPath('choosedb.ui'), self )
		self.type = type
		if type == ChooseDatabaseDialog.TypeSelect:
			self.uiDatabaseEditor.setVisible( False )
			self.uiDatabaseLabel.setBuddy( self.uiDatabaseSelector )
		else:
			self.uiDatabaseSelector.setVisible( False )
			self.uiDatabaseLabel.setBuddy( self.uiDatabaseEditor )

		host = options.options['login.server']
		port = options.options['login.port']
		secure = options.options['login.secure']
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
		res = askserver.refreshDatabaseList(self.uiDatabaseSelector, str( self.uiServer.text() ) )
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
		if self.type == ChooseDatabaseDialog.TypeSelect:
			self.databaseName = str( self.uiDatabaseSelector.currentText() )
		else:
			self.databaseName = str( self.uiDatabaseEditor.text() )
		self.password = str( self.uiPassword.text() )
		self.accept()
		
	def slotChange(self):
		dialog = askserver.AskServer(self)
		dialog.setDefault( str( self.uiServer.text() ) )
		if dialog.exec_() == QDialog.Accepted:
			self.uiServer.setText( dialog.url )
			self.refreshList()

