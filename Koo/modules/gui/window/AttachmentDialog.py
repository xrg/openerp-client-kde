#############################################################################
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

from Common import common
from FormWidget import *

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import * 


class AttachmentDialog(QMainWindow):

	def __init__(self, model, id, parent = None ):	
		QMainWindow.__init__(self, parent)
		loadUi( common.uiPath('win_attach.ui'), self ) 

		# Center dialog on the screen
		rect = QApplication.desktop().screenGeometry()
		centerh = rect.width() / 2
		centerv = rect.height() / 2
		self.setGeometry( centerh - self.width() / 2, centerv - self.height() / 2, self.width(), self.height() )

		self.model = model
		self.id = id

		self.form = form.form( 'ir.attachment', view_type=['tree','form'], domain=[('res_model','=',self.model), ('res_id', '=', self.id)])
		self.form.setAllowOpenInNewWindow( False )

		self.layout = self.centralWidget().layout()
		self.layout.addWidget( self.form )

		# These actions are not handled by the Main Window but by the currently opened tab.
		# What we do here, is connect all these actions to a single handler that will
		# call the current child/tab/form. This is handled this way instead of signals because we
		# may have several windows opened at the same time and all children would receive
		# the signal...
		self.actions = [ 'New', 'Save', 'Delete', 'Next', 'Previous', 'Switch' ]
		for x in self.actions:
			action = eval('self.action' + x)
			self.connect( action, SIGNAL('triggered()'), self.callChildView )
		self.connect( self.actionClose, SIGNAL('triggered()'), self.slotClose )
		self.updateEnabledActions()

	def updateEnabledActions(self):
		for x in self.actions:
			action = eval( 'self.action' + x )
			action.setEnabled( x in self.form.handlers )

	def callChildView( self  ):
		o = self.sender()	
		action = str( o.objectName() ).replace( 'action', '' )
		res = True
		if action in self.form.handlers:
			res = self.form.handlers[action]()

	def slotClose( self ):
		if self.form.canClose():
			self.close()
			# We need this so the window will be deleted (resources freed)
			# and destroyed() signal will be sent. This way the caller can
			# update the number of attachments for the current model.
			self.deleteLater()

