from PyQt4.QtGui import *
from PyQt4.QtCore import *
import service
import rpc

class TinyAction(QAction):
	def __init__(self, parent):
		QAction.__init__(self, parent)
		self._data = None
		self._type = None 

	def setData(self, data):
		self._data = data

	def data(self):
		return self._data

	def setType(self, type):
		self._type = type

	def type(self):
		return self._type

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

		obj = service.LocalService('action.main')
		obj._exec_action(self._data, {}, {})

	def executeAction(self, currentId, ids):
		if not currentId and not ids:
			QMessageBox.information(self, '', _('You must save this record to use the relate button !'))
			return False
			
		if not currentId:
			currentId = ids[0]
		elif not ids:
			ids = [currentId]
		obj = service.LocalService('action.main')
		obj._exec_action(self._data, { 'id': currentId, 'ids': ids } )

class ActionFactory:
	@staticmethod
	def create(parent, definition):
		if not definition:
			return
		actions = []
		for icontype in ( 'print','action','relate' ):
			for tool in definition[icontype]:
				action = TinyAction( parent )
				action.setIcon( QIcon( ":/images/images/%s.png" % icontype) )
				action.setText( tool['string'] )
				action.setType( icontype )
				action.setData( tool )
				actions.append( action )
		return actions

