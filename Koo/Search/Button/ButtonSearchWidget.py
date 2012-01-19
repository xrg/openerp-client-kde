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

from Koo.Common import Common

from Koo import Rpc

from Koo.Search.AbstractSearchWidget import AbstractSearchWidget
from PyQt4.QtGui import QPushButton, QVBoxLayout, QIcon
from Koo.Common import Icons
#from PyQt4.QtCore import *

class ButtonSearchWidget(AbstractSearchWidget):
	def __init__(self, name, parent, attributes=None):
		if attributes is None:
			attributes = {}
		AbstractSearchWidget.__init__(self, name, parent, attributes)
		self.pushButton = QPushButton( self )
		self.pushButton.setText( attributes.get('string', '') )
		self.pushButton.setCheckable( True )
		layout = QVBoxLayout( self )
		if 'icon' in attributes:
                    self.pushButton.setIcon( Icons.kdeIcon( attributes['icon'] ))

		layout.addWidget( self.pushButton )
		layout.setSpacing( 0 )
		layout.setContentsMargins( 0, 0, 0, 0 )
		self.focusWidget = self.pushButton

		self.domain = attributes.get('domain', "[]")
		self.context = attributes.get('context', "{}")

	def value(self):
		return Rpc.session.evaluateExpression( self.domain, Rpc.session.context )

	def clear(self):
                self.pushButton.setChecked(False)
		self.pushButton.setDown( False )

	def setValue(self, value):
		pass

# vim:noexpandtab:smartindent:tabstop=8:softtabstop=8:shiftwidth=8:
