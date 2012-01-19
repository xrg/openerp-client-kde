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

from Koo.Search.AbstractSearchWidget import *
from PyQt4.QtGui import *
from PyQt4.QtCore import QVariant

class SelectionSearchWidget(AbstractSearchWidget):
	def __init__(self, name, parent, attrs={}):
		AbstractSearchWidget.__init__(self, name, parent, attrs)
		self.uiCombo = QComboBox( self )
		self.uiCombo.setEditable( False )

		self.layout = QHBoxLayout( self )
		self.layout.addWidget( self.uiCombo )
		self.layout.setSpacing( 0 )
		self.layout.setContentsMargins( 0, 0, 0, 0 )

		self.fill( attrs.get('selection',[] ) )
		self.focusWidget = self.uiCombo
		
	def fill(self, selection):
		# The first is a blank element
		self.uiCombo.addItem( '' )
		for (id,name) in selection:
			self.uiCombo.addItem( name, QVariant(id) )

	def value( self ):
		value = self.uiCombo.itemData( self.uiCombo.currentIndex() )
		if value.isValid():
                    if value.type() == QVariant.Int:
                        return [(self.name,'=',value.toInt()[0] )]
                    elif value.type() == QVariant.LongLong:
                        return [(self.name,'=',value.toLongLong()[0] )]
                    else:
                        return [(self.name,'=',unicode(value.toString()) )]
		else:
			return []

	def setValue(self, value):
		if not value:
			self.uiCombo.setCurrentIndex( self.uiCombo.findText('') )
		else:
			self.uiCombo.setCurrentIndex( self.uiCombo.findData( QVariant(value) ) )

	def clear(self):
		self.setValue( False )

