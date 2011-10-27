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
from Koo.Common.Ui import *
from Koo import Rpc
from Koo.Common import Common
from Koo.Model.Group import RecordGroup
from Koo.Screen.ViewQueue import *
from Koo.Screen.Screen import *

(BatchInsertDialogUi, BatchInsertDialogBase) = loadUiType( Common.uiPath('batchupdate.ui') )

class BatchInsertDialog( QDialog, BatchInsertDialogUi ):
	def __init__( self, parent=None ):
		QDialog.__init__(self, parent)
		BatchInsertDialogUi.__init__(self)
		self.setupUi( self )
		
		self.connect( self.pushAccept, SIGNAL('clicked()'), self.save )

		self.ids = []
		self.model = None
		self.context = None
		self.updateOnServer = True
		self.newValues = {}
		self.availableFields = []

	def setModel(self, model):
		self.model = model

	def setContext(self, context):
		self.context = context

	def setAvailableFields(self, fields):
		self.availableFields = fields

	def setUpdateOnServer(self, update):
		self.updateOnServer = update

	def setViewTypes(self, viewTypes):
		self.viewTypes = viewTypes

	def setViewIds(self, viewIds):
		self.viewIds = viewIds

	def setup(self):
		fields = Rpc.session.execute('/object', 'execute', self.model, 'fields_view_get', False, 'form', Rpc.session.context)
		fields = fields['fields']
		if self.availableFields:
			for field in fields.keys():
				if not field in self.availableFields:
					del fields[field]
				
		oneToManyFields = [(fields[field]['string'], field) for field in fields if fields[field]['type'] == 'many2one']
		oneToManyFields = dict(oneToManyFields)
		selectionDialog = Common.SelectionDialog(_('Choose field to insert in batch action'), oneToManyFields, self)
		if selectionDialog.exec_() == QDialog.Rejected:
			return False
		fieldString = selectionDialog.result[0]
		fieldName = selectionDialog.result[1]
		self.newField = fieldName
		fieldModel = fields[fieldName]['relation']
		fields = {
			'many2many': {
				'string': fieldString,
				'name': 'many2many',
				'type': 'many2many',
				'relation': fieldModel,
			}
		}
		arch = ''
		arch += '<?xml version="1.0"?>'
		arch += '<form string="%s">\n' % _('Batch Insert')
		arch += '<label string="%s" colspan="4"/>' % fieldString
		arch += '<field name="many2many" colspan="4" nolabel="1"/>'
		arch += '</form>'
		group = RecordGroup( fieldModel, fields )
		self.screen.setRecordGroup( group )
		self.screen.new(default=False)
		self.screen.addView(arch, fields, display=True)
		return True

	def createScreen(self):
		self.group = RecordGroup( self.model, context=self.context )
		self.group.setDomainForEmptyGroup()

		screen = Screen()
		screen.setRecordGroup( self.group )
		screen.setEmbedded( True )
		if 'form' in self.viewTypes:
			queue = ViewQueue()	
			queue.setup( self.viewTypes, self.viewIds )	
			type = ''
			while type != 'form':
				id, type = queue.next()
			screen.setupViews( ['form'], [id] )
		else:
			screen.setupViews( ['form'], [False] )

	def save( self ):
                self.screen.currentView().store()
                record = self.screen.currentRecord()
		self.newValues = [x.id for x in record.value('many2many')]
                if record.isModified() and self.newValues:
			if QMessageBox.question(self, _('Batch Insert'), _('Are you sure you want to insert %d records?') % len(self.newValues), _("Yes"), _("No")) == 1:
				return
			if self.updateOnServer:
				screen = self.createScreen()
				for value in self.newValues:
					record = self.group.create()
					record.setValue( self.newField, value )
				self.group.save()
		self.accept()

