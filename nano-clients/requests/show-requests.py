#!/usr/bin/python

from common import localization
localization.initializeTranslations()

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
		tree.setRootIsDecorated( False )
		layout.addWidget(tree)
		layout.setMargin( 0 )
		self.resize(600, 300)

		rpc.session.login( 'http://admin:admin@127.0.0.1:8069', 'jornadas' )
		
		# Example of asynchronous call:
		# The function 'called()' will be called twice in this example,
		# one for the signal and another one for the callback. Of course,
		# only one method is needed.
		call = rpc.AsynchronousSessionCall( rpc.session, self )
		self.connect( call, SIGNAL('called(PyQt_PyObject)'), self.called )
		call.call( self.called, '/object', 'execute', 'res.partner', 'search', [] )

		visible = ['create_date', 'name', 'act_from', 'act_to', 'body' ]
		self.fields = rpc.session.execute('/object', 'execute', 'res.request', 'fields_get', visible)
		ids = rpc.session.execute('/object', 'execute', 'res.request', 'search', [])
		self.group = ModelRecordGroup( 'res.request', self.fields, ids )
		treeModel = TreeModel( self )
		treeModel.setModelGroup( self.group )
		treeModel.setFields( self.fields )
		treeModel.setShowBackgroundColor( False )

		tree.setModel( treeModel )

	def called(self, obj):
		print "Returned: ", obj


app = QApplication(sys.argv)
localization.initializeQtTranslations()

r = RequestsDialog()

r.show()
app.exec_()
