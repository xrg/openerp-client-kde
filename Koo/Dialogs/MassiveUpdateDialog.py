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

(MassiveUpdateDialogUi, MassiveUpdateDialogBase) = loadUiType( Common.uiPath('massiveupdate.ui') )

class MassiveUpdateDialog( QDialog, MassiveUpdateDialogUi ):
	def __init__( self, parent=None ):
		QDialog.__init__(self, parent)
		MassiveUpdateDialogUi.__init__(self)
		self.setupUi( self )
		
		self.connect( self.pushAccept, SIGNAL('clicked()'), self.save )

		self.ids = []

	def setIds( self, ids ):
		self.ids = ids

	def setup( self, model, context ):
		self.model = model
		self.context = context
		self.group = RecordGroup( self.model, context=self.context )
		self.group.setAllowRecordLoading( False )

		self.screen.setModelGroup( self.group )
		self.screen.setEmbedded( True )
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
				fields.append( '<li>%s</li>' % name )

			fields.sort()
			fields = '<ul>%s</ul>' % ''.join( fields )

		if fields:
			answer = QMessageBox.question( self, _('Confirmation'), 
				_('<p>This process will update the following fields in %(number)d records:</p>%(records)s<p>Do you want to continue?</p>') % { 
				'number': len(self.ids), 
				'records': fields 
				}, QMessageBox.Yes | QMessageBox.No )
			if answer == QMessageBox.No:
				return
                        Rpc.session.execute('/object', 'execute', self.model, 'write', self.ids, values, self.context)
		self.accept()

