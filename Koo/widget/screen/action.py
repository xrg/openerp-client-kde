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

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from Common import api
from Plugins import *
import Rpc

class TinyAction(QAction):
	def __init__(self, parent):
		QAction.__init__(self, parent)
		self._data = None
		self._type = None 
		self._model = None

	def setData(self, data):
		self._data = data

	def data(self):
		return self._data

	def setType(self, type):
		self._type = type

	def type(self):
		return self._type

	def setModel(self, model):
		self._model = model

	def model(self):
		return self._model

	def execute(self, currentId, selectedIds):
		if self._type == 'relate':
			self.executeRelate( currentId )
		elif self._type in ( 'action', 'print' ):
			self.executeAction( currentId, selectedIds )
		else:
			self.executePlugin( currentId, selectedIds )

	def executeRelate(self, currentId):
		if not currentId:
			QMessageBox.information( self, '', _('You must select a record to use the relate button !'))
		api.instance.executeAction(self._data, {'id': currentId})

	def executeAction(self, currentId, ids):
		if not currentId and not ids:
			QMessageBox.information(self, '', _('You must save this record to use the relate button !'))
			return False
			
		if not currentId:
			currentId = ids[0]
		elif not ids:
			ids = [currentId]
		api.instance.executeAction(self._data, { 'id': currentId, 'ids': ids, 'model': self._model } )
		
	def executePlugin(self, currentId, ids):
		Plugins.execute( self._data, self._model, currentId, ids )

class ActionFactory:
	@staticmethod
	def create(parent, definition, model):
		if not definition:
			# If definition is not set we initialize it appropiately
			# to be able to add the 'Print Screen' action.
			definition = {
				'print': [],
				'action': [],
				'relate': []
			}

		# We always add the 'Print Screen' action.
		definition['print'].append({
			'name': 'Print Screen', 
			'string': _('Print Screen'), 
			'report_name': 'printscreen.list', 
			'type': 'ir.actions.report.xml' 
		})

		actions = []
		for icontype in ( 'print','action','relate' ):
			for tool in definition[icontype]:
				action = TinyAction( parent )
				action.setIcon( QIcon( ":/images/images/%s.png" % icontype) )
				action.setText( tool['string'] )
				action.setType( icontype )
				action.setData( tool )
				action.setModel( model )
				actions.append( action )

		plugs = Plugins.list()
		for p in plugs:
			action = TinyAction( parent )
			action.setIcon( QIcon( ":/images/images/exec.png" ) )
			action.setText( unicode( plugs[p]['string'] ) )
			action.setData( p )
			action.setType( 'plugin' )
			action.setModel( model )
			actions.append( action )

		return actions

