#!/usr/bin/python

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
