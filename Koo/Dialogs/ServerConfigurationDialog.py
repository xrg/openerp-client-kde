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
from Koo.Common.Ui import *
import re
from Koo.Common import Common
from Koo.Common.Settings import *
from Koo import Rpc

# Searches the list of available databases in the server
def refreshDatabaseList(widget, url, dbtoload=None):
	if not dbtoload:
		dbtoload = Settings.value('login.db')
	index = 0
	widget.clear()
		
	result = Rpc.database.list(url)
	if result == False:
		return -2
	if result == -1:
		return -1
	if result:
		for db_num, db_name in enumerate(result):
			widget.addItem( db_name )
			if db_name == dbtoload:
				index = db_num
	widget.setCurrentIndex(index)
	return widget.count()

(ServerConfigurationDialogUi, ServerConfigurationDialogBase) = loadUiType( Common.uiPath('change_server.ui') )

class ServerConfigurationDialog( QDialog, ServerConfigurationDialogUi ):
	url = ''

	def __init__(self, parent=None):
		QDialog.__init__(self, parent)
		ServerConfigurationDialogUi.__init__(self)
		self.setupUi(self)

		if Rpc.isNetRpcAvailable:
			self.uiConnection.addItem( _("NET-RPC"), QVariant( 'socket' ) )
		self.uiConnection.addItem( _("XML-RPC"), QVariant( 'http' ) )
		self.uiConnection.addItem( _("Secure XML-RPC"), QVariant( 'https' ) )
		if Rpc.isPyroAvailable:
			self.uiConnection.addItem( _("Pyro (faster)"), QVariant( 'PYROLOC' ) )
		if Rpc.isPyroSslAvailable:
			self.uiConnection.addItem( _("Pyro SSL (faster)"), QVariant( 'PYROLOCSSL' ) )
		result = False
		self.connect(self.pushCancel,SIGNAL("clicked()"),self.reject )
		self.connect(self.pushAccept,SIGNAL("clicked()"),self.slotAccept )

	def setUrl( self, url ):
		self.url = url
		url = QUrl( url )
		if url.isValid():
			self.uiConnection.setCurrentIndex( self.uiConnection.findData( QVariant( url.scheme() ) ) )
			self.uiServer.setText( url.host() )
			self.uiPort.setText( unicode( url.port() ) )

	def slotAccept(self):
		url = QUrl( self.url )
		protocol = unicode( self.uiConnection.itemData( self.uiConnection.currentIndex() ).toString() )
		url.setScheme( protocol )
		url.setHost( self.uiServer.text() )
		url.setPort( int( self.uiPort.text().toInt()[0] ) )
		if url.isValid():
			# Store default settings
			Settings.setValue('login.url', unicode( url.toString() ) )
			Settings.saveToFile()
		url.setUserName( '' )
		self.url = unicode( url.toString() )
		self.accept()

# vim:noexpandtab:smartindent:tabstop=8:softtabstop=8:shiftwidth=8:
