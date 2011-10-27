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

from Koo.Common import Common

from Koo.Common.Calendar import *
from Koo.Search.AbstractSearchWidget import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from Koo.Common.Ui import *

class TimeSearchWidget(AbstractSearchWidget):
	def __init__(self, name, parent, attrs={}):
		AbstractSearchWidget.__init__(self, name, parent, attrs)
		self.uiStart = QLineEdit( self )
		label = QLabel( "-", self)
		self.uiEnd = QLineEdit( self )
		layout = QHBoxLayout( self )
		layout.setContentsMargins( 0, 0, 0, 0 )
		layout.setSpacing( 0 )
		layout.addWidget(self.uiStart)
		layout.addWidget(label)
		layout.addWidget(self.uiEnd)

		# Catch keyDownPressed
		self.uiStart.installEventFilter( self )
		self.uiEnd.installEventFilter( self )

		self.focusWidget = self.uiStart

	def _getTime(self, text):
		time = textToTime( text )
		if time.isValid():
			return str( time.toString( 'hh:mm:ss' ) )
		else:
			return False

	def value(self):
		res = []
		val = self._getTime( str( self.uiStart.text() ) )
 		if val:
			res.append((self.name, '>=', val ))
		else:
			self.uiStart.clear()
		val = self._getTime( str( self.uiEnd.text()) )
	 	if val:
			res.append((self.name, '<=', val ))
		else:
			self.uiEnd.clear()
		return res

	def clear(self):
		self.uiStart.clear()
		self.uiEnd.clear()

	def setValue(self, value):
		if value:
			self.uiStart.setText( unicode(value) )
			self.uiEnd.setText( unicode(value) )
		else:
			self.uiStart.clear()
			self.uiEnd.clear()

