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

from Koo import Rpc
from FieldPreferencesDialog import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *

class AbstractFieldDelegate(QStyledItemDelegate):
	def __init__(self, parent, attributes):
		QStyledItemDelegate.__init__(self, parent)
		self.name = attributes['name']
		self.attributes = attributes
		self.colors = {
			'invalid'  : '#FF6969',
			'readonly' : '#e3e3e3', 
			'required' : '#ddddff', 
			'normal'   : 'white'
		}

	def createEditor(self, parent, option, index):
		# We expecte a KooModel here
		model = index.model().modelFromIndex( index )
		if model and not model.isFieldValid( self.name ):
			name = 'invalid'
		elif self.attributes.get('readonly', False):
			name = 'readonly'
		elif self.attributes.get('required', False):
			name = 'required'
		else:
			name = 'normal'
		editor = QStyledItemDelegate.createEditor( self, parent, option, index )
		color = QColor( self.colors.get( name, 'white' ) )
		palette = QPalette()
		palette.setColor(QPalette.Base, color)
		editor.setPalette(palette);
		return editor

	# Use this function to return the menuEntries your widget wants to show
	# just before the context menu is shown. Return a list of tuples in the form:
	# [ (_('Menu text'), function/slot to connect the entry, True (for enabled) or False (for disabled) )] 
	def menuEntries(self):
		return []

