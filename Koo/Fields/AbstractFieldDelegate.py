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

## @brief AbstractFieldDelegate is the base class for all delegates used in Koo.
# Delegates are used by editable lists but could be used by any Model/View based
# widget.
class AbstractFieldDelegate(QStyledItemDelegate):
	## @brief Creates a new Delegate. 
	# 'attributes' is a dictionary with attributes that apply to the field such
	# as 'readonly' or 'required'.
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
		self.defaultMenuEntries = [
			#(_('Set to default value'), self.setToDefault, 1),
		]

	def createEditor(self, parent, option, index):
		# We expecte a KooModel here
		model = index.model().recordFromIndex( index )
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

	## @brief Use this function to return the menu entries your delegate wants to show
	# just before the context menu is shown. Return a list of tuples in the form:
	# [ (_('Menu text'), function/slot to connect the entry, True (for enabled) or False (for disabled) )] 
	def menuEntries(self, record):
		return []

	## @brief Shows a popup menu with default and widget specific
	# entries.
	def showPopupMenu(self, parent, position):
		# parent is supposed to be a QAbstractItemView
		index = parent.indexAt( parent.mapFromGlobal( position ) )
		if not index or not index.isValid():
			return
		record = index.model().recordFromIndex( index )

		entries = self.defaultMenuEntries[:]
		new = self.menuEntries( record )
		if len(new) > 0:
			entries = entries + [(None, None, None)] + new
		if not entries:
			return
		menu = QMenu( parent )
		for title, slot, enabled in entries:
			if title:
				item = QAction( title, menu )
				if slot:
					self.connect( item, SIGNAL("triggered()"), slot )
				item.setEnabled( enabled )
				menu.addAction( item )
			else:
				menu.addSeparator()
		menu.popup( position )

	## @brief Sets the default value to the field.
	#
	# Note that this requires a call to the server.
	def setToDefault(self):
		try:
			model = self.record.group.resource
			res = Rpc.session.call('/object', 'execute', model, 'default_get', [self.attrs['name']])
			self.record.setValue(self.name, res.get(self.name, False))
			self.display()
		except:
			QMessageBox.warning(None, _('Operation not permited'), _('You can not set to the default value here !') )
			return False
