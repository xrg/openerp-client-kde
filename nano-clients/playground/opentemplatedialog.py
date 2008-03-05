from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *
import rpc
from widget.model.group import *
from widget.model.treemodel import *

class OpenTemplateDialog(QDialog):
	def __init__(self, parent=None):
		QDialog.__init__(self, parent)
		loadUi( 'opentemplate.ui', self )

		visible = ['name', 'boxes']
		self.fields = rpc.session.execute('/object', 'execute', 'nan.template', 'fields_get', visible)
		ids = rpc.session.execute('/object', 'execute', 'nan.template', 'search', [])
		self.group = ModelRecordGroup( 'nan.template', self.fields, ids )
		self.treeModel = TreeModel( self )
		self.treeModel.setModelGroup( self.group )
		self.treeModel.setFields( self.fields )
		self.treeModel.setShowBackgroundColor( False )
		self.treeModel.setMode( TreeModel.ListMode )
		self.treeModel.setFieldsOrder( ['name', 'boxes'] )

		self.treeView.setModel( self.treeModel )

		self.connect( self.pushOpen, SIGNAL('clicked()'), self.open )

	def open(self):
		index = self.treeView.selectionModel().currentIndex()
		self.id = self.treeModel.id(index)
		self.accept()
