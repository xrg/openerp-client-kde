##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id: textbox.py 4751 2006-12-01 14:50:46Z ced $
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
from PyQt4.QtCore import *
from PyQt4.QtGui import *

class TextBoxFormWidget(AbstractFormWidget):
	def __init__(self, parent, model, attrs={}):
		AbstractFormWidget.__init__(self, parent, model, attrs)
		self.setSizePolicy( QSizePolicy.Expanding, QSizePolicy.Expanding )
		self.uiText = QTextEdit( self )
		self.uiText.setSizePolicy( QSizePolicy.Expanding, QSizePolicy.Expanding )
		self.installPopupMenu( self.uiText )
		layout = QHBoxLayout( self )
		layout.setContentsMargins( 0, 0, 0, 0 )
		layout.addWidget( self.uiText )

	def setReadOnly(self, value):
		self.uiText.setReadOnly( value )

	def colorWidget(self):
		return self.uiText

	def store(self):
		self.model.setValue(self.name, unicode( self.uiText.document().toPlainText() ) or False )

	def clear(self):
		self.uiText.clear()

	def showValue(self):
		value = self.model.value(self.name)
		if not value:
			self.uiText.clear()
		else:
			self.uiText.setText( value )

