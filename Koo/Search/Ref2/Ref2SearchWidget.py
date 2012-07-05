##############################################################################
#
# Copyright (c) 2007-2008 Albert Cervera i Areny <albert@nan-tic.com>
# Copyright (C) 2012 P. Christeas <xrg@hellug.gr>
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

from Koo.Search.AbstractSearchWidget import *
from PyQt4.QtGui import *

class Ref2SearchWidget(AbstractSearchWidget):
	def __init__(self, name, parent, attrs={}):
		AbstractSearchWidget.__init__(self, name, parent, attrs)
		self.layout = QHBoxLayout( self )
		self.layout.setSpacing( 0 )
		self.layout.setContentsMargins( 0, 0, 0, 0 )
		self.uiText = QLineEdit( self )
		self.layout.addWidget( self.uiText )
		self.focusWidget = self.uiText
		# Catch keyDownPressed
		self.focusWidget.installEventFilter( self )

	def value(self):
		s = unicode(self.uiText.text())
		if s:
			return [(self.name,self.attrs.get('comparator','ilike'),s)]
		else:
			return []

	def clear(self):
		self.uiText.clear()

	def setValue(self, value):
                if isinstance(value, (int, long)):
                    value = ''
                elif isinstance(value, (tuple, list)): 
                    #Note: tuple is rare, won't make it through RPC
                    if len(value) >= 2:
                        value = value[1]
                    else:
                        value = ''
		self.uiText.setText( value )

#eof