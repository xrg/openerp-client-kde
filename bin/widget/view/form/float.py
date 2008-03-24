##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id: spinbutton.py 4173 2006-09-28 15:33:48Z ged $
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

from abstractformwidget import *
from common.numeric import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *


class FloatFormWidget(AbstractFormWidget):
	def __init__(self, parent, model, attrs={}):
 		AbstractFormWidget.__init__(self, parent, model, attrs)

		self.widget = QLineEdit(self)
		layout = QHBoxLayout( self )
		layout.setContentsMargins( 0, 0, 0, 0 )
		layout.addWidget( self.widget )

		self.installPopupMenu( self.widget )
		self.connect( self.widget, SIGNAL('editingFinished()'), self.calculate )
		self.setState('valid')
		self.digits = attrs.get('digits', None)

	def setReadOnly(self, value):
		self.widget.setEnabled( not value )

	def calculate(self):
		val = textToFloat( str(self.widget.text() ) )
		if val:
			self.widget.setText( str(val) )
		else:
			self.clear()
		self.modified()

	def value(self):
		return textToFloat( str(self.widget.text()) )

	def store(self):
		self.model.setValue( self.name, self.value() )

	def clear(self):
		self.widget.setText('')
		
	def showValue(self):
		if self.model.value(self.name):
			self.widget.setText( floatToText( self.model.value(self.name), self.digits ) )
		else:
			self.clear()

	def colorWidget(self):
		return self.widget

