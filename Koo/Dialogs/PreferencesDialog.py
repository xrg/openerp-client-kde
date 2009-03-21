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
from PyQt4.uic import *

from Koo import Rpc

from Koo.Common import Common
import copy

from Koo.Screen.Screen import Screen
from Koo.Model.Group import ModelRecordGroup

(PreferencesDialogUi, PreferencesDialogBase) = loadUiType( Common.uiPath('preferences.ui') )

class PreferencesDialog(QDialog, PreferencesDialogUi):
	def __init__(self, model, id, preferences, parent=None):
		QDialog.__init__(self, parent)
		PreferencesDialogUi.__init__(self)
		self.setupUi( self )

		self.id = id
		self.model = model
		
		self.connect( self.pushAccept, SIGNAL('clicked()'), self.slotAccept )
		fields = {}
		arch = '<?xml version="1.0"?><form string="%s">\n' % (_('Preferences'),)
		for p in preferences:
			arch+='<field name="%s" colspan="4"/>' % (p[1])
			fields[p[1]] = p[3]
		arch+= '</form>'

		self.screen = Screen( self )
		self.screen.setModelGroup( ModelRecordGroup( model ) )
		self.screen.new(default=False)
		self.screen.addView(arch, fields, display=True)

		default = Rpc.session.execute('/object', 'execute', 'ir.values', 'get', 'meta', False, [(self.model,self.id)], False, Rpc.session.context, True, True, False)
		default2 = {}
		self.default = {}
		for d in default:
			default2[d[1]] = d[2]
			self.default[d[1]] = d[0]
		self.screen.currentRecord().set(default2)

		self.layout().insertWidget( 0, self.screen )

		self.setWindowTitle(_('Preference %s') % model )

	def slotAccept(self):
		if not self.screen.currentRecord().validate():
			return
		val = copy.copy(self.screen.get())

		for key in val:
			if val[key]:
				Rpc.session.execute('/object', 'execute', 'ir.values', 'set', 'meta', key, key, [(self.model,self.id)], val[key])
			elif self.default.get(key, False):
				Rpc.session.execute('/common', 'ir_del', self.default[key])
		self.accept()
		
