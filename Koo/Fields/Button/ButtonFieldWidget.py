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
from Koo.Fields.AbstractFieldWidget import *
from Koo.Common import Api
from Koo.Common import Notifier
from Koo.Common import Icons
from Koo.Common import Common

class ButtonFieldWidget( AbstractFieldWidget ):
	def __init__(self, parent, view, attributes) :
		AbstractFieldWidget.__init__( self, parent, view, attributes )

		self.button = QPushButton( self )
		layout = QHBoxLayout(self)
		layout.setContentsMargins(0, 0, 0, 0)
		layout.addWidget( self.button )

		self.button.setText( Common.normalizeLabel( attributes.get('string', 'unknown' ) ) )
		if 'icon' in attributes:
			self.button.setIcon( Icons.kdeIcon( attributes['icon'] ))
	
		self.connect( self.button, SIGNAL('clicked()'), self.click)

	def click( self ): 
		# TODO: Remove screen dependency and thus ViewForm.screen
		screen = self.view.screen
		self.view.store()
		if self.model.validate():
			id = screen.save()
			if not self.attrs.get('confirm',False) or \
					QMessageBox.question(self,_('Question'),self.attrs['confirm'],QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
				type = self.attrs.get('type', 'workflow')
				if type == 'workflow':
					QApplication.setOverrideCursor( Qt.WaitCursor )
					Rpc.session.execute('/object', 'exec_workflow', screen.name, self.name, id)
					QApplication.restoreOverrideCursor()
				elif type == 'object':
					QApplication.setOverrideCursor( Qt.WaitCursor )
					Rpc.session.execute('/object', 'execute', screen.name, self.name, [id], self.model.context())
					QApplication.restoreOverrideCursor()
				elif type == 'action':
					action_id = int(self.attrs['name'])
					Api.instance.execute(action_id, {'model':screen.name, 'id': id, 'ids': [id]})
				else:
					Notifier.notifyError( _('Error in Button'), _('Button type not allowed'), _('Button type not allowed') )

				QApplication.setOverrideCursor( Qt.WaitCursor )
				screen.reload()
				QApplication.restoreOverrideCursor()
		else:
			Notifier.notifyWarning('',_('Invalid Form, correct red fields!'))
			screen.display()

	def setReadOnly(self, value):
		self.button.setEnabled( not value )

	def display(self, state):
		if self.attrs.get('states', False):
			states = self.attrs.get('states', '').split(',')
			if state not in states:
				self.hide()
			else:
				self.show()
		else:
			self.show()


