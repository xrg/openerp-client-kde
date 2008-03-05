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

		visible = ['name']
		self.fields = rpc.session.execute('/object', 'execute', 'nan.template', 'fields_get', visible)
		ids = rpc.session.execute('/object', 'execute', 'nan.template', 'search', [])
		self.group = ModelRecordGroup( 'nan.template', self.fields, ids )
		treeModel = TreeModel( self )
		treeModel.setModelGroup( self.group )
		treeModel.setFields( self.fields )
		treeModel.setShowBackgroundColor( False )

		self.treeView.setModel( treeModel )

		self.connect( self.pushOpen, SIGNAL('clicked()'), self.open )

	def open(self):
		self.accept()
