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
import re
from Common import common
from Common import options
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

class ServerConfigurationDialog( QDialog ):
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

