##############################################################################
#
# Copyright (c) 2004 TINY SPRL. (http://tiny.be) All Rights Reserved.
#                    Fabien Pinckaers <fp@tiny.Be>
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

import gettext
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from Koo.Common.Ui import *

from Koo import Rpc

from Koo.Common import Common
from Koo.Common.Settings import *
import copy

from Koo.Screen.Screen import Screen
from Koo.Model.Group import RecordGroup

(PreferencesDialogUi, PreferencesDialogBase) = loadUiType( Common.uiPath('preferences.ui') )

class PreferencesDialog(QDialog, PreferencesDialogUi):
	def __init__(self, parent=None):
		QDialog.__init__(self, parent)
		PreferencesDialogUi.__init__(self)
		self.setupUi( self )

		self.connect( self.pushAccept, SIGNAL('clicked()'), self.slotAccept )

		self.setWindowTitle( _('User Preferences') )
		QApplication.setOverrideCursor( Qt.WaitCursor )
		QTimer.singleShot( 0, self.initGui )

	def initGui(self):
		actionId = Rpc.session.execute('/object', 'execute', 'res.users', 'action_get', {})
		action = Rpc.session.execute('/object', 'execute', 'ir.actions.act_window', 'read', [actionId], False, Rpc.session.context)[0]

		viewIds=[]
		if action.get('views', []):
			viewIds=[x[0] for x in action['views']]
		elif action.get('view_id', False):
			viewIds=[action['view_id'][0]]

		self.group = RecordGroup('res.users')
		self.group.load( [Rpc.session.uid] )
		self.screen.setRecordGroup( self.group )
		self.screen.setupViews( ['form'], [viewIds[0]] )
		self.screen.display( Rpc.session.uid )

		# Adjust size and center the dialog
		self.adjustSize()
		if self.parent():
			rect = self.parent().geometry()
		else:
			rect = QApplication.desktop().availableGeometry( self )
		self.move( rect.x() + (rect.width() / 2) - (self.width() / 2), 
				rect.y() + (rect.height() / 2) - (self.height() / 2) )

		QApplication.restoreOverrideCursor()

	def slotAccept(self):
		if not self.screen.currentRecord().validate():
			return

		if self.screen.currentRecord().fieldExists( 'context_lang' ):
			Settings.setValue( 'client.language', self.screen.currentRecord().value( 'context_lang' ) )
			Settings.saveToFile()

		Rpc.session.execute('/object', 'execute', 'res.users', 'write', [Rpc.session.uid], self.screen.get())
		Rpc.session.reloadContext()
		self.accept()
