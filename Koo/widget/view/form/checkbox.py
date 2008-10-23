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

from abstractformwidget import *
from PyQt4.QtGui import *

class CheckBoxFormWidget(AbstractFormWidget):
	def __init__(self, parent, model, attrs={}):
		AbstractFormWidget.__init__(self, parent, model, attrs)
		self.setSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed )
		self.widget = QCheckBox( self )
		self.widget.setSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed )
		layout = QHBoxLayout( self )
		layout.setContentsMargins( 0, 0, 0, 0 )
		layout.setSpacing( 0 )
		layout.addWidget( self.widget )
		self.installPopupMenu( self.widget )
		self.connect( self.widget, SIGNAL('stateChanged(int)'), self.callModified )

	def callModified(self, value):
		self.modified()

	def setReadOnly(self, value):
		self.widget.setEnabled( not value )

	def store(self):
		self.model.setValue(self.name, self.widget.isChecked())

	def clear(self):
		self.widget.setChecked(False)

	def showValue(self):
		self.widget.setChecked(self.model.value(self.name))

	def colorWidget(self):
		return self.widget

