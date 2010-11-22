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
from PyQt4.uic import *
from Koo import Rpc
from Koo.Common import Common
from Koo.Model.Group import RecordGroup
from Koo.Screen.ViewQueue import *

(MassiveUpdateMessageBoxUi, MassiveUpdateMessageBoxBase) = loadUiType( Common.uiPath('massiveupdate_msgbox.ui') )

class MassiveUpdateMessageBoxDialog(QDialog, MassiveUpdateMessageBoxUi):
	def __init__(self, parent=None):
		QDialog.__init__(self, parent)
		MassiveUpdateMessageBoxUi.__init__(self)
		self.setupUi(self)
		self._fields = []

	def setMessage(self, message):
		self.uiMessage.setText( message )

	def setFields(self, fields):
		"""
		fields = [(label, name)...]
		"""
		self._fields = fields
		for field in self._fields:
			item = QListWidgetItem( self.uiFields )
			item.setText( field[0] )
			item.setSelected( True )
			self.uiFields.addItem( item )

	def selectedFields(self):
		selected = []
		for x in xrange(self.uiFields.count()):
			item = self.uiFields.item(x)
			if item.isSelected():
				selected.append( self._fields[x][1] )
		return selected


(MassiveUpdateDialogUi, MassiveUpdateDialogBase) = loadUiType( Common.uiPath('massiveupdate.ui') )

class MassiveUpdateDialog( QDialog, MassiveUpdateDialogUi ):
	def __init__( self, parent=None ):
		QDialog.__init__(self, parent)
		MassiveUpdateDialogUi.__init__(self)
		self.setupUi( self )
		
		self.connect( self.pushAccept, SIGNAL('clicked()'), self.save )

		self.ids = []
		self.model = None
		self.context = None
		self.updateOnServer = True
		self.newValues = {}

	def setIds( self, ids ):
		self.ids = ids

	def setModel(self, model):
		self.model = model

	def setContext(self, context):
		self.context = context

	def setUpdateOnServer(self, update):
		self.updateOnServer = update

	def setup( self, viewTypes, viewIds ):
		self.group = RecordGroup( self.model, context=self.context )
		self.group.setDomainForEmptyGroup()

		self.screen.setRecordGroup( self.group )
		self.screen.setEmbedded( True )
		if 'form' in viewTypes:
			queue = ViewQueue()	
			queue.setup( viewTypes, viewIds )	
			type = ''
			while type != 'form':
				id, type = queue.next()
			self.screen.setupViews( ['form'], [id] )
		else:
			self.screen.setupViews( ['form'], [False] )
		self.screen.new()

	def save( self ):
                self.screen.currentView().store()
                record = self.screen.currentRecord()
		fields = []
                if record.isModified():
			values = record.get(get_readonly=False, get_modifiedonly=True)
			for field in values:
				attrs = record.fields()[ field ].attrs
				if 'string' in attrs:
					name = attrs['string']
				else:
					name = field
				fields.append( (name, field) )

			fields.sort(key=lambda x: x[0])

			if fields:
				messageBox = MassiveUpdateMessageBoxDialog(self)
				messageBox.setFields(fields)
				messageBox.setMessage( _('Select the fields you want to update in the <b>%d</b> selected records:') % len(self.ids) )
				if messageBox.exec_() == QDialog.Rejected:
					return
				self.newValues = {}
				for field in messageBox.selectedFields():
					self.newValues[field] = values[field]

				if self.updateOnServer:
					Rpc.session.execute('/object', 'execute', self.model, 'write', self.ids, self.newValues, self.context)
		self.accept()

