from PyQt4.QtGui import *
from PyQt4.QtCore import *
from common import api
import rpc

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
		elif self._type in ( 'action','print' ):
			self.executeAction( currentId, selectedIds )
		else:
			print "Unknown action"

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
		return actions

