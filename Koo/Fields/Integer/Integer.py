##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
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

from Koo.Fields.AbstractFieldWidget import *
from Koo.Fields.AbstractFieldDelegate import *
from Koo.Common.Numeric import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *

class IntegerFieldWidget(AbstractFieldWidget):
	def __init__(self, parent, model, attrs={}):
		AbstractFieldWidget.__init__(self, parent, model, attrs)
		self.widget = QLineEdit( self )
		self.widget.setSizePolicy( QSizePolicy.Preferred, QSizePolicy.Fixed )
		layout = QHBoxLayout( self )
		layout.setContentsMargins( 0, 0, 0, 0 )
		layout.addWidget( self.widget )
		self.connect( self.widget, SIGNAL('editingFinished()'), self.calculate )
		self.installPopupMenu( self.widget )

	def calculate(self):
		val = textToInteger( unicode(self.widget.text() ) )
		self.setText( integerToText(val) )
		self.modified()

	def value(self):
		return textToInteger( unicode(self.widget.text()) )

	def store(self):
		self.record.setValue(self.name, self.value() )

	def clear(self):
		self.setText('0')

	def showValue(self):
		value = self.record.value( self.name )
		self.setText( str(value) )

	def setReadOnly(self, value):
		AbstractFieldWidget.setReadOnly(self, value)
		self.widget.setReadOnly( value )

	def colorWidget(self):
		return self.widget

	def setText(self, text):
		self.widget.setText( text )
		self.widget.setCursorPosition( 0 )

class IntegerFieldDelegate( AbstractFieldDelegate ):
	def setModelData(self, editor, model, index):
		value = textToInteger( unicode( editor.text() ) )
		model.setData( index, QVariant( value ), Qt.EditRole )

