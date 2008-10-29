##############################################################################
#
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

from AbstractSearchWidget import *
from PyQt4.QtGui import *
from PyQt4.uic import *
from Koo.Common import Common

class ReferenceSearchWidget(AbstractSearchWidget):
	def __init__(self, name, parent, attrs={}):
		AbstractSearchWidget.__init__(self, name, parent, attrs)
		loadUi( Common.uiPath('searchreference.ui'), self )
		self.setPopdown( attrs.get('selection',[]) )
		self.focusWidget = self.uiModel

	def setPopdown(self, selection):
		self.invertedModels = {}
		for (i,j) in selection:
			self.uiModel.addItem( j, QVariant(i) )
			self.invertedModels[i] = j

	def getValue(self):
		resource = unicode(self.uiModel.itemData(self.uiModel.currentIndex()).toString())
		if resource:
			return [(self.name, 'like', resource + ',')]
		else:
			return []


	def setValue(self, value):
		model, (id, name) = value
		self.uiModel.setCurrentIndex( self.uiModel.findText(self.invertedModels[model]) )

	value = property(getValue, setValue, None,
	  'The content of the widget or ValueError if not valid')

	def clear(self):
		self.value = ''

