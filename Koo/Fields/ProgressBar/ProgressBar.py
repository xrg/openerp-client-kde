##############################################################################
#
# Copyright (c) 2008 Albert Cervera i Areny <albert@nan-tic.com>
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

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from Koo.Common import Common
from Koo.Fields.AbstractFieldWidget import *
from Koo.Fields.AbstractFieldDelegate import *


class ProgressBarFieldWidget(AbstractFieldWidget):
	def __init__(self, parent, view, attrs={}):
		AbstractFieldWidget.__init__(self, parent, view, attrs)

		self.uiBar = QProgressBar( self )
		self.uiBar.setMinimum( 0 )
		self.uiBar.setMaximum( 100 )
		layout = QHBoxLayout( self )
		layout.setContentsMargins( 0, 0, 0, 0 )
		layout.addWidget( self.uiBar )

		self.installPopupMenu( self.uiBar )

	def clear(self):
		self.uiBar.reset()

	def showValue(self):
		value = self.model.value(self.name)
		if not value:
			self.clear()
		value = max( min( value, 100 ), 0 )
		self.uiBar.setValue( value )

class ProgressBarFieldDelegate( AbstractFieldDelegate ):

	def createEditor(self, parent, option, index):
		return None

	def paint(self, painter, option, index):
		# Paint background
		itemOption = QStyleOptionViewItemV4(option)
		QApplication.style().drawControl(QStyle.CE_ItemViewItem, itemOption, painter)

		# Paint ProgressBar
		opts = QStyleOptionProgressBarV2()
		opts.rect = option.rect
		opts.minimum = 1
		opts.maximum = 100
		opts.textVisible = True
		percent, ok = index.data(Qt.DisplayRole).toDouble()
		percent = max( min( percent, 100 ), 0 )
		opts.progress = percent
		opts.text = QString( '%d%%' % percent )
		QApplication.style().drawControl(QStyle.CE_ProgressBar, opts, painter)

