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

from Common import Common
from Common.Numeric import *

from AbstractSearchWidget import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.uic import *

class IntegerSearchWidget(AbstractSearchWidget):
	def __init__(self, name, parent, attrs={}):
		AbstractSearchWidget.__init__(self, name, parent, attrs)
		layout = QHBoxLayout( self )
		layout.setSpacing( 0 )
		layout.setContentsMargins( 0, 0, 0, 0 )
		self.uiStart = QLineEdit( self )
		label = QLabel( '-', self )
		self.uiEnd = QLineEdit( self )
		layout.addWidget( self.uiStart )
		layout.addWidget( label )
		layout.addWidget( self.uiEnd )
		self.connect( self.uiStart, SIGNAL('returnPressed()'), self.calculate )
		self.connect( self.uiEnd, SIGNAL('returnPressed()'), self.calculate )
		self.focusWidget = self.uiStart

	def calculate(self):
		widget = sender()
		val = textToInteger( str(widget.text() ) )
		if val:
			widget.setText( str(val) )
		else:
			widget.clear()

	def getValue(self):
		res = []
		start = textToInteger( str(self.uiStart.text()) )
		end = textToInteger( str(self.uiEnd.text()) )
		if start and not end:
			res.append((self.name, '=', start))
			return res
		if start:
			res.append((self.name, '>=', start))
		if end:
			res.append((self.name, '<=', end))
		return res

	def setValue(self, value):
		if value:
			self.uiStart.setText( str(value) )
		else:
			self.uiStart.clear()
		if value:
			self.uiEnd.setText( str(value) ) 
		else:
			self.uiEnd.clear()

	value = property(getValue, setValue, None,
	  'The content of the widget or ValueError if not valid')

	def clear(self):
		self.value = False
		self.uiStart.clear()
		self.uiEnd.clear()

