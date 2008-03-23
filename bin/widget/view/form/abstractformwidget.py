##############################################################################
#
# Copyright (c) 2004 TINY SPRL. (http://tiny.be) All Rights Reserved.
#					Fabien Pinckaers <fp@tiny.Be>
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

import rpc
from fieldpreferences import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *

_attrs_boolean = {
	'required': False,
	'readonly': False
}

# In order to create a new form widget, that is: a widget that appears in a 
# auto-generated form you need to inherit from this class and implement some
# of it's functions.
#
# The Widget handles a field from a record. You can access the record
# using the property 'model' and the field name using the property 'name'
#
class AbstractFormWidget(QWidget):

	# The constructor receives the following parameters
	#  parent:     The QWidget parent of this QWidget
	#  view:       Holds the reference to the view the widget is in
	#  attributes: Holds some extra attributes such as read-only and others
	def __init__(self, parent, view, attributes):
		QWidget.__init__(self, parent)

		self.attrs = attributes
		self.view = view

		for key,val in _attrs_boolean.items():
			self.attrs[key] = self.attrs.get(key, False) not in ('False', '0', False)
		self.defaultReadOnly= self.attrs.get('readonly', False)
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
		self.name = self.attrs['name']
		self.model = None

		# Some widgets might want to change their color set.
		self.colors = {
			'invalid'  : '#ffdddd', 
			'readonly' : '#e3e3e3', 
			'required' : '#ddddff', 
			'normal'   : 'white'
		}

	def setToDefault(self):
		try:
			model = self.model.resource
			res = rpc.session.call('/object', 'execute', model, 'default_get', [self.attrs['name']])
			model = self.model.setValue(self.name, res.get(self.name, False))
			self.display()
		except:
			QMessageBox.warning(None, _('Operation not permited'), _('You can not set to the default value here !') )
			return False

	def setAsDefault(self):
		if not self.view:
			return
		deps = []
		wid = self.view.widgets
		for wname, wview in self.view.widgets.items():
			if wview.attrs.get('change_default', False):
				value = wview.model.value(wview.name)
				deps.append((wname, wname, value, value))
		value = self.model.default( self.name )
		model = self.model.resource
		dialog = FieldPreferencesDialog(self.attrs['name'], self.attrs.get('string', self.attrs['name']), model, value, deps)
		dialog.exec_()

	def refresh(self):
		self.setReadOnly(self.attrs.get('readonly', False))
		if self.attrs.get('readonly', False):
			self.setColor('readonly')
		elif not self.attrs.get('valid', True):
			self.setColor('invalid')
		elif self.attrs.get('required', False):
			self.setColor('required')
		else:
			self.setColor('normal')

	# It's called when the widget has to be Read-Only. When implementing a
	# new widget, please use setEnabled( not ro ) instead of read-only. The
	# gray color gives information to the user so she knows the field can't

# be modified
	def setReadOnly(self, ro):
		pass

	def isReadOnly(self):
		return self.attrs.get('readonly', False)

	# Use it in your widget to return the widget in which you want the color 
	# indicating the obligatory, normal, ... etc flags to be set. 
	def colorWidget(self):
		return self

	# Use this function to return the menuEntries your widget wants to show
	# just before the context menu is shown. Return a list of tuples in the form:
	# [ (_('Menu text'), function/slot to connect the entry, True (for enabled) or False (for disabled) )] 
	def menuEntries(self):
		return []

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

	def setState(self, state):
		state_changes = dict(self.attrs.get('states',{}).get(state,[]))
		for key, value in state_changes.items():
			self.attrs[key] = value
		else:
			if 'readonly' not in state_changes:
				self.attrs['readonly'] = self.defaultReadOnly

	## @brief Installs the eventFilter on the given widget so the popup
	# menu will be shown on ContextMenu event.
	def installPopupMenu( self, widget ):
		widget.installEventFilter( self )

	def eventFilter( self, target, event ):
		if event.type() == QEvent.ContextMenu:
			self.showPopupMenu( target, event.globalPos() )
			return True
		if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Tab:
			#e = QKeyEvent( event.type(), event.key(), event.modifiers(), event.text(), event.isAutoRepeat(), event.count() )
			##QCoreApplication.postEvent( self, e )
			#self.event( e )
			#event.ignore()
			print "Sending events!!!"
			#return True
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

	# Call this function/slot when your widget changes the
	# value. This is needed for the onchange option in the 
	# server modules. Usually you'll call it on lostFocus if
	# there's a TextBox or on selection, etc.
	def modified(self):
		if not self.model:
			return 
		self.store()

	# Override this function. This will be called by display()
	# when it wants the value to be shown in the widget
	def showValue(self):
		pass

	# Override this function. It will be used whenever there
	# is no model or have created a new record.
	def clear(self):
		pass

	# Do not reimplement this function, override showValue() instead
	def display(self, state='draft'):
		if not self.model:
			self.attrs['readonly'] = True
			self.clear()
			self.refresh()
			return
		self.setState(state)
		self.refresh()
		self.showValue()
	
	def reset(self):
		if 'valid' in self.attrs:
			self.attrs['valid'] = True
		self.refresh()

	# TODO: I don't see a reason for this function. It seems it should
	# propagate the on_change signal... Will need a deeper look.
	# Maybe, simply by testing if the server onchange option works.
	def sig_changed(self):
		if self.attrs.get('on_change',False):
			self.view.screen.on_change(self.attrs['on_change'])

	def load(self, model, state = 'draft' ):
		self.model = model
		self.display(state)

	def store(self):
		pass

