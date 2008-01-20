##############################################################################
#
# Copyright (c) 2004 TINY SPRL. (http://tiny.be) All Rights Reserved.
#                    Fabien Pinckaers <fp@tiny.Be>
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

from common import common

from abstractsearchwidget import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.uic import *

class reference(AbstractSearchWidget):
	def __init__(self, name, parent, attrs={}):
		AbstractSearchWidget.__init__(self, name, parent, attrs)
		loadUi( common.uiPath('reference.ui'), self )
		self.model = attrs['args']

		self.wid_text = self.widget.ent_reference
		self._value=None
		self.focusWidget = self.wid_text

	def sig_activate(self, *args):
		self.wid_id.set_text(str(self._value[0]))

	def sig_changed(self, *args):
		self.wid_id.set_text('-')
	
	def _value_get(self):
		if self._value:
			return self._value[0]
		else:
			return False

	def _value_set(self, value):
		self._value = value
		if self.value!=False:
			self.wid_text.set_text( value[1] )
			self.wid_id.set_text( str(value[0]) )
		else:
			self.wid_text.set_text( '' )
			self.wid_id.set_text( '' )

	value = property(_value_get, _value_set, None,
	  'The content of the widget or ValueError if not valid')

	def clear(self, widget=None):
		self.value = False
