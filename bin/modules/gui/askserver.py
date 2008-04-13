from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *
import re
from common import common
from common import options
import rpc

# Searches the list of available databases in the server
def refreshDatabaseList(db_widget, url, dbtoload=None):
	if not dbtoload:
		dbtoload = options.options['login.db']
	index = 0
	db_widget.clear()
		
	result = rpc.database.list(url)
	if result == -1:
		return -1
	if result:
		for db_num, db_name in enumerate(result):
			db_widget.addItem( db_name )
			if db_name == dbtoload:
				index = db_num
	db_widget.setCurrentIndex(index)
	return db_widget.count()

class AskServer( QDialog ):
	url = ''

	def __init__(self, parent=None):
		QDialog.__init__(self, parent)
		loadUi( common.uiPath('change_server.ui'), self ) 
		self.uiConnection.addItem( _("NET-RPC (faster)"), QVariant( 'socket://' ) )
		self.uiConnection.addItem( _("XML-RPC"), QVariant( 'http://' ) )
		self.uiConnection.addItem( _("Secure XML-RPC"), QVariant( 'https://' ) )
		result = False
		self.connect(self.pushCancel,SIGNAL("clicked()"),self.reject )
		self.connect(self.pushAccept,SIGNAL("clicked()"),self.slotAccept )

	def setDefault( self, url ):
		self.url = url
		m = re.match('^(http[s]?://|socket://)([\w.\-]+):(\d{1,5})$', url )
		if m:
			self.uiConnection.setCurrentIndex( self.uiConnection.findData( QVariant( m.group(1) ) ) )
			self.uiServer.setText( m.group(2) )
			self.uiPort.setText( m.group(3) )

	def slotAccept(self):
		protocol = unicode( self.uiConnection.itemData( self.uiConnection.currentIndex() ).toString() )
		self.url = '%s%s:%s' % (protocol, self.uiServer.text(), self.uiPort.text())
		self.accept()

