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
from Common import common
import Rpc

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *

class FieldPreferencesDialog( QDialog ):
	def __init__(self, field, name, model, value, dependance=[], parent=None):
		QDialog.__init__( self, parent )
		loadUi( common.uiPath('field_preferences.ui'), self )
		self.uiFieldName.setText( name )
		self.uiDomain.setText( model )
		self.uiDefaultValue.setText( (value and unicode(value)) or '/' )

		self.model = model
		self.field = field
		self.value = value
		frameLayout = QVBoxLayout( self.uiFrame )
		self.widgets = {}
		for (fname, fvalue, rname, rvalue) in dependance:
			w = QCheckBox(self)
			w.setText( fname + ' = ' + str(rname) )
			self.widgets[(fvalue,rvalue)] = w
			frameLayout.addWidget( w )
		if not len(dependance):
			frameLayout.addWidget(QLabel(_('<center>Always applicable!</center>'), self))
		self.connect( self.pushAccept, SIGNAL('clicked()'), self.slotAccept )

	def slotAccept(self):
		deps = False
		for x in self.widgets.keys():
			if self.widgets[x].isChecked():
				deps = x[0] + '=' + str(x[1])	
				break
		Rpc.session.execute('/object', 'execute', 'ir.values', 'set', 'default', deps, self.field, [(self.model,False)], self.value, True, False, False, self.uiOnlyForYou.isChecked())
		self.accept()

