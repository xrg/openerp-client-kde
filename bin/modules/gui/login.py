from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *
#import options
from common import common
import askserver

class LoginDialog( QDialog ):
	defaultHost = ''
	defaultPort = 0
	defaultProtocol = ''
	defaultUserName = ''

	def __init__(self, parent=None ):
		QDialog.__init__(self, parent)
		loadUi( common.uiPath('login.ui'), self ) 
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
		#host = options.options['login.server']
		#port = options.options['login.port']
		#protocol = options.options['login.protocol']
		host = LoginDialog.defaultHost
		port = LoginDialog.defaultPort
		protocol = LoginDialog.defaultProtocol
		url = '%s%s:%s' % (protocol, host, port)
		self.uiServer.setText( url )
		#self.uiUserName.setText( options.options['login.login'] )
		self.uiUserName.setText( LoginDialog.defaultUserName )
		res = self.refreshList()

	def refreshList(self):
		res = askserver.refreshDatabaseList(self.uiDatabase, str( self.uiServer.text() ), self.databaseName )
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
		dialog = askserver.AskServer( self )
		dialog.setDefault( str( self.uiServer.text() ) )
		dialog.exec_()
		self.uiServer.setText( dialog.url )
		self.refreshList()

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

