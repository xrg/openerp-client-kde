#!/usr/bin/python

import rpc
from widget.model.field import *
from widget.model.record import *
from widget.model.group import *
from widget.model.treemodel import *

import sys
from PyQt4.QtGui import *

class RequestsDialog(QDialog):
	def __init__(self,parent=None):
		QDialog.__init__(self,parent)
		layout = QVBoxLayout(self)
		tree = QTreeView(self)
		layout.addWidget(tree)

		rpc.session.login( 'http://admin:admin@127.0.0.1:8069', 'graficas' )
		visible = ['create_date', 'name', 'act_from', 'act_to', 'body' ]
		self.fields = rpc.session.execute('/object', 'execute', 'res.request', 'fields_get', visible)
		ids = rpc.session.execute('/object', 'execute', 'res.request', 'search', [])
		self.group = ModelRecordGroup( 'res.request', self.fields, ids )
		treeModel = TreeModel( self )
		treeModel.setModelGroup( self.group )
		treeModel.setFields( self.fields )
		treeModel.setShowBackgroundColor( False )
		tree.setModel( treeModel )


app = QApplication(sys.argv)

r = RequestsDialog()

r.show()
app.exec_()
