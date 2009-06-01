##############################################################################
#
# Copyright (c) 2004 TINY SPRL. (http://tiny.be) All Rights Reserved.
#					Fabien Pinckaers <fp@tiny.Be>
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

from Koo import Rpc
from FieldPreferencesDialog import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *


## @brief AbstractFieldWidget is the base class for all widgets in Koo.
# In order to create a new form widget, that is: a widget that appears in a 
# auto-generated form you need to inherit from this class and implement some
# of it's functions.
#
# The Widget handles a field from a record. You can access the record
# using the property 'record' and the field name using the property 'name'.
#
class AbstractFieldWidget(QWidget):

	## @brief Creates a new AbstractFieldWidget and receives the following parameters
	#  parent:     The QWidget parent of this QWidget
	#  view:       Holds the reference to the view the widget is in
	#  attributes: Holds some extra attributes such as read-only and others
	def __init__(self, parent, view, attributes):
		QWidget.__init__(self, parent)

		self.attrs = attributes
		self.view = view

		if 'visible' in self.attrs:
			self.setVisible( bool(int(self.attrs['visible'])) )

		# Required and readonly attributes are not directly linked to
		# the field states because a widget might not have a record
		# assigned. Also updating the attribute directly in the fields
		# can cause some problems with stateAttributes.
		self._required = self.attrs.get('required', False) not in ('False', '0', False)
		self._readOnly = self.attrs.get('readonly', False) not in ('False', '0', False)

		self.defaultReadOnly= self._readOnly
		self.defaultMenuEntries = [
			(_('Set to default value'), self.setToDefault, 1),
		]

		# As currently slotSetDefault needs view to be set we use it
		# only in form views.
		if self.view:
			self.defaultMenuEntries.append( (_('Set as default value'), self.setAsDefault, 1) )

		if 'stylesheet' in self.attrs:
			self.setStyleSheet( self.attrs['stylesheet'] )

		# self.name holds the name of the field the widget handles
		self.name = self.attrs.get('name', 'unnamed')
		self.record = None

		# Some widgets might want to change their color set.
		self.colors = {
			'invalid'  : '#FF6969',
			'readonly' : '#e3e3e3', 
			'required' : '#ddddff', 
			'normal'   : 'white'
		}

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

	## @brief Opens the FieldPreferencesDialog to set the current value as default for this field.
	def setAsDefault(self):
		if not self.view:
			return
		deps = []
		wid = self.view.widgets
		for wname, wview in self.view.widgets.items():
			if wview.attrs.get('change_default', False):
				value = wview.record.value(wview.name)
				deps.append((wname, wname, value, value))
		value = self.record.default( self.name )
		model = self.record.group.resource
		dialog = FieldPreferencesDialog(self.attrs['name'], self.attrs.get('string', self.attrs['name']), model, value, deps)
		dialog.exec_()

	## @brief Updates the background color depending on widget state.
	#
	# Possible states are: invalid, readonly, required and normal.
	def refresh(self):
		self.setReadOnly( self._readOnly )
		if self.record and not self.record.isFieldValid( self.name ):
			self.setColor('invalid')
		elif self._readOnly:
			self.setColor('readonly')
		elif self._required:
			self.setColor('required')
		else:
			self.setColor('normal')

	## @brief This function is called when the widget has to be Read-Only. 
	# When implementing a new widget, please use setEnabled( not ro ) instead 
	# of read-only. The gray color gives information to the user so she knows 
	# the field can't be modified
	def setReadOnly(self, ro):
		pass

	## @brief This function returns True if the field is read-only. False otherwise.
	def isReadOnly(self):
		return self._readOnly

	## @brief Use it in your widget to return the widget in which you want the color 
	# indicating the obligatory, normal, ... etc flags to be set. 
	# By default colorWidget() returns self.
	def colorWidget(self):
		return self

	## @brief Use this function to return the menuEntries your widget wants to show
	# just before the context menu is shown. Return a list of tuples in the form:
	# [ (_('Menu text'), function/slot to connect the entry, True (for enabled) or False (for disabled) )] 
	def menuEntries(self):
		return []

	## @brief Sets the background color to the widget returned by colorWidget(). 
	# name should contain the current state ('invalid', 'readonly', 'required' or 'normal')
	#
	# The appropiate color for each state is stored in self.colors dictionary.
	def setColor(self, name):
		# Set the appropiate property so it can be used
		# in stylesheets
		self.setProperty('invalid', QVariant(False))
		self.setProperty('readonly', QVariant(False))
		self.setProperty('required', QVariant(False))
		self.setProperty('normal', QVariant(False))
		self.setProperty(name, QVariant(True))

		widget = self.colorWidget()
		color = QColor( self.colors.get( name, 'white' ) )

		palette = QPalette()
		palette.setColor(QPalette.Base, color)
		widget.setPalette(palette);

	## @brief Installs the eventFilter on the given widget so the popup
	# menu will be shown on ContextMenu event. Also data on the widget will
	# be stored in the record when the widget receives the FocusOut event.
	def installPopupMenu( self, widget ):
		widget.installEventFilter( self )

	## @brief Reimplements eventFilter to show the context menu and store
	# information when the widget loses the focus. This function will be
	# used on the widget you give to installPopupMenu.
	def eventFilter( self, target, event ):
		if event.type() == QEvent.ContextMenu:
			self.showPopupMenu( target, event.globalPos() )
			return True
		if event.type() == QEvent.FocusOut:
			if self.record:
				self.store()
		return False

	## @brief Shows a popup menu with default and widget specific
	# entries.
	def showPopupMenu(self, parent, position):
		entries = self.defaultMenuEntries[:]
		new = self.menuEntries()
		if len(new) > 0:
			entries = entries + [(None, None, None)] + new
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

	## @brief Call this function/slot when your widget changes the
	# value. This is needed for the onchange option in the 
	# server modules. Usually you'll call it on lostFocus if
	# there's a TextBox or on selection, etc.
	def modified(self):
		if not self.record:
			return 
		self.store()

	## @brief Override this function. This will be called by display()
	# when it wants the value to be shown in the widget
	def showValue(self):
		pass

	## @brief Override this function. It will be used whenever there
	# is no model or have created a new record.
	def clear(self):
		pass

	## @brief This function displays the current value of the field in the record 
	# in the widget.
	#
	# Do not reimplement this function, override clear() and showValue() instead
	def display(self):
		if not self.record:
			self._readOnly = True
			self.clear()
			self.refresh()
			return
		self._readOnly = self.record.isFieldReadOnly(self.name)
		self._required = self.record.isFieldRequired(self.name)
		self.refresh()
		self.showValue()
	
	def reset(self):
		self.refresh()

	## @brief Sets the current record for the widget.
	def load(self, record ):
		self.record = record
		self.display()

	## @brief Stores information in the widget to the record.
	# Reimplement this function in your widget.
	def store(self):
		pass

