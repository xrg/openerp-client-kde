##############################################################################
#
# Copyright (c) 2010 Albert Cervera i Areny <albert@nan-tic.com>
#                    http://www.NaN-tic.com
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

from xml.parsers import expat

import sys
import gettext

from SearchWidgetFactory import *
from AbstractSearchWidget import *
from Koo.Common import Common
from Koo.Common import Shortcuts
from Koo.Common import Calendar
from Koo.Common import Numeric
from Koo.Common.Ui import *
from Koo import Rpc

from PyQt4.QtGui import *
from PyQt4.QtCore import *

class SearchFormContainer( QWidget ):
	def __init__(self, parent):
		QWidget.__init__( self, parent )
		layout = QGridLayout( self )
		layout.setSpacing( 0 )
		layout.setContentsMargins( 0, 0, 0, 0 )
		# Maximum number of columns
		self.col = 4
		self.x = 0
		self.y = 0

	def addWidget(self, widget, name=None):
		if self.x + 1 > self.col:
			self.x = 0
			self.y = self.y + 1

		# Add gridLine attribute to all widgets so we can easily discover
		# in which line they are.
		widget.gridLine = self.y
		if name:
			label = QLabel( name )
			label.gridLine = self.y
			vbox = QVBoxLayout()
			vbox.setSpacing( 0 )
			vbox.setContentsMargins( 0, 0, 0, 0 )
			vbox.addWidget( label, 0 )
			vbox.addWidget( widget )
			self.layout().addLayout( vbox, self.y, self.x )
		else:
                	self.layout().addWidget( widget, self.y, self.x )
		self.x = self.x + 1

(CustomSearchItemWidgetUi, CustomSearchItemWidgetBase) = loadUiType( Common.uiPath('customsearchitem.ui') )

class CustomSearchItemWidget(AbstractSearchWidget, CustomSearchItemWidgetUi):

	# Structure:
	#   1) Operator used in domain
	#   2) Label shown to the user
	#   3) Field types in which the operator should be shown
	#   4) Whether the user should be able to input a text to search for or not.
	operators = (
		('is empty', _('is empty'), ('selection', 'char', 'text', 'many2one', 'date', 'time', 'datetime', 'float_time', 'binary'), False),
		('is not empty', _('is not empty'), ('selection', 'char', 'text', 'many2one', 'date', 'time', 'datetime', 'float_time', 'binary'), False),
		('ilike', _('contains'), ('char','text','many2one','many2many','one2many'), True), 
		('not ilike', _('does not contain'), ('char','text','many2one'), True), 
		('=', _('is equal to'), ('boolean','char','text','integer','float','date','time','datetime','float_time','user'), True),
		('<>', _('is not equal to'), ('boolean','char','text','integer','float','date','time','datetime','float_time'), True), 
		('>', _('greater than'), ('char','text','integer','float','date','time','datetime','float_time'), True), 
		('<', _('less than'), ('char','text','integer','float','date','time','datetime','float_time'), True), 
		('>=', _('greater or equal to'), ('char','text','integer','float','date','time','datetime','float_time'), True), 
		('<=', _('less or equal to'), ('char','text','integer','float','date','time','datetime','float_time'), True), 
		('in', _('in'), ('selection','char','text','integer','float','date','time','datetime','float_time'), True),
		('not in', _('not in'), ('selection','char','text','integer','float','date','time','datetime','float_time'), True),
		('starts_with', _('starts with'), ('char','text'), True),
		('ends_with', _('ends with'), ('char','text'), True),
		('=ilike', _('similar to'), ('char','text'), True),
	)

	typeRelated = ('many2one','many2many','one2many')

	def __init__(self, parent=None):
		AbstractSearchWidget.__init__(self, '', parent)
		CustomSearchItemWidgetUi.__init__(self)
		self.setupUi(self)

		self.uiRelatedField.setVisible( False )
		self.connect(self.uiField, SIGNAL('currentIndexChanged(int)'), self.updateRelatedAndOperators)
		self.connect(self.uiRelatedField, SIGNAL('currentIndexChanged(int)'), self.updateOperators)
		self.connect(self.uiOperator, SIGNAL('currentIndexChanged(int)'), self.updateValue)

		self.fields = None
		self.andOr = 'and'

	def setup(self, fields):
		self.uiField.addItem( '' )

		self.fields = fields

		fields = [(x, fields[x].get('string', x)) for x in fields]
		fields.sort( key=lambda x: x[1] )
		for field in fields:
			self.uiField.addItem( field[1], QVariant( field[0] ) )


		self.uiOperator.addItem( '' )
		for operator in self.operators:
			self.uiOperator.addItem( operator[1], QVariant( operator[0] ) )

		self.scNew = QShortcut( self )
		self.scNew.setKey( Shortcuts.CreateInField )
		self.scNew.setContext( Qt.WidgetWithChildrenShortcut )

		self.scRemove = QShortcut( self )
		self.scRemove.setKey( Shortcuts.ClearInField )
		self.scRemove.setContext( Qt.WidgetWithChildrenShortcut )

		self.setAndSelected()

		self.connect( self.scNew, SIGNAL('activated()'), self, SIGNAL('newItem()') )
		self.connect( self.pushNew, SIGNAL('clicked()'), self, SIGNAL('newItem()') )
		self.connect( self.pushAndOr, SIGNAL('clicked()'), self.toggleAndOr )
		self.connect( self.scRemove, SIGNAL('activated()'), self, SIGNAL('removeItem()') )
		self.connect( self.pushRemove, SIGNAL('clicked()'), self, SIGNAL('removeItem()') )

	def setValid(self, valid):
		if valid:
			color = 'white'
		else:
			color = 'red'
		color = QColor( color )
		palette = QPalette()
		palette.setColor(QPalette.Active, QPalette.Base, color)
		self.setPalette(palette);

	def setAndSelected(self):
		self.pushAndOr.setText( _('&And') )
		self.andOr = 'and'

	def setOrSelected(self):
		self.pushAndOr.setText( _('&Or') )
		self.andOr = 'or'

	def isAndSelected(self):
		return self.andOr == 'and'

	def isOrSelected(self):
		return self.andOr == 'or'

	def copyState(self, widget):
		if widget.isAndSelected():
			self.setAndSelected()
		else:
			self.setOrSelected()

	def toggleAndOr(self):
		if self.isAndSelected():
			self.setOrSelected()
		else:
			self.setAndSelected()

	def updateRelatedAndOperators(self, index=None):
		fieldName = unicode( self.uiField.itemData( self.uiField.currentIndex() ).toString() )
		if not fieldName:
			return

		fieldType = self.fields[fieldName].get('type')

		if fieldType in self.typeRelated:
			self.uiRelatedField.setVisible( True )
			self.uiRelatedField.setCurrentIndex( 0 )
			model = self.fields[fieldName].get('relation')
			if model:
				view = Rpc.session.execute('/object', 'execute', model, 'fields_view_get', False, 'form', Rpc.session.context)
				self.relatedFields = view['fields']
			else:
				self.relatedFields = {}

			self.uiRelatedField.clear()
			self.uiRelatedField.addItem( '', QVariant('') )
			fields = [(x, self.relatedFields[x].get('string', x)) for x in self.relatedFields]
			fields.sort( key=lambda x: x[1] )
			for field in fields:
				self.uiRelatedField.addItem( field[1], QVariant( field[0] ) )
		else:
			self.uiRelatedField.clear()
			self.uiRelatedField.setVisible( False )

		self.updateOperators()

	def updateOperators(self, index=None):
		self.uiOperator.clear()
		fieldName = unicode( self.uiField.itemData( self.uiField.currentIndex() ).toString() )
		relatedFieldName = unicode( self.uiRelatedField.itemData( self.uiRelatedField.currentIndex() ).toString() )
		if not fieldName:
			return

		if relatedFieldName:
			fieldType = self.relatedFields[relatedFieldName].get('type')
		else:
			fieldType = self.fields[fieldName].get('type')

		self.uiOperator.addItem( '' )
		for operator in self.operators:
			if fieldType in operator[2]:
				self.uiOperator.addItem( operator[1], QVariant( operator[0] ) )


	def updateValue(self, index):
		operator = unicode( self.uiOperator.itemData( self.uiOperator.currentIndex() ).toString() )
		for op in self.operators:
			if operator == op[0]:
				self.uiValue.setVisible( op[3] )
				break
		self.setValid( True )

	def clear(self):
		self.uiField.setCurrentIndex( 0 )
		self.uiRelatedField.clear()
		self.uiOperator.setCurrentIndex( 0 )
		self.uiValue.clear()

	def correctValue(self, value, fieldName, relatedFieldName):
		text = value

		if relatedFieldName:
			fieldType = self.relatedFields[relatedFieldName].get('type')
		else:
			fieldType = self.fields[fieldName].get('type')
		if fieldType == 'date':
			value = Calendar.textToDate( value )
			text = Calendar.dateToText( value )
			value = Calendar.dateToStorage( value )
		elif fieldType == 'datetime':
			value = Calendar.textToDateTime( value )
			text = Calendar.dateTimeToText( value )
			value = Calendar.dateTimeToStorage( value )
		elif fieldType == 'float_time':
			value = Calendar.textToFloatTime( value )
			text = Calendar.floatTimeToText( value )
			value = Calendar.floatTimeToStorage( value )
		elif fieldType == 'time':
			value = Calendar.textToTime( value )
			text = Calendar.timeToText( value )
			value = Calendar.timeToStorage( value )
		elif fieldType == 'float':
			value = Numeric.textToFloat( value ) or 0.0
			text = Numeric.floatToText( value )
		elif fieldType == 'integer':
			value = Numeric.textToInteger( value ) or 0.0
			text = Numeric.integerToText( value )
		elif fieldType == 'selection':

			if relatedFieldName:
				options = self.relatedFields[relatedFieldName]['selection']
			else:
				options = self.fields[fieldName]['selection']

			text = []
			keys = []
			for selection in options:
				# If text matches exactly one of the options of the selection field
				# do not 'accept' other options. Otherwise, all options that contain
				# the text will be 'accepted'.
				if value.lower().strip() == selection[1].lower().strip():
					keys = [ selection[0] ]
					text = [ selection[1] ]
					break
				if value.lower() in selection[1].lower():
					keys.append( selection[0] )
					text.append( selection[1] )
			value = keys
			text = ', '.join( text )
		elif fieldType == 'boolean':
			options = [
				(True, _('True')),
				(False, _('False')),
			]
			text = ''
			for selection in options:
				if value.lower() in selection[1].lower():
					value = selection[0]
					text = selection[1]
					break
			if not text:
				value = options[1][0]
				text = options[1][1]
		return (value, text)

	def value(self):
		if not self.uiField.currentIndex():
			return []
		if not self.uiOperator.currentIndex():
			self.setValid( False )
			return []
		self.setValid( True )
		fieldName = unicode( self.uiField.itemData( self.uiField.currentIndex() ).toString() )
		relatedFieldName = unicode( self.uiRelatedField.itemData( self.uiRelatedField.currentIndex() ).toString() )
		operator = unicode( self.uiOperator.itemData( self.uiOperator.currentIndex() ).toString() )
		value = unicode( self.uiValue.text() )
		fieldType = self.fields[fieldName].get('type')
		
		if operator in ('in', 'not in'):
			text = []
			newValue = []
			for item in value.split(','):
				data = self.correctValue( item.strip(), fieldName, relatedFieldName )
				newValue.append( data[0] )
				text.append( data[1] )
			value = newValue
			text = ', '.join( text )

			newValue = []
			for item in value:
				if isinstance(item, list):
					newValue += [x for x in item]
				else:
					newValue.append( item )
			value = newValue
		elif operator == 'is empty':
			operator = '='
			value = False
			text = ''
		elif operator == 'is not empty':
			operator = '!='
			value = False
			text = ''
		else:
			(value, text) = self.correctValue( value, fieldName, relatedFieldName )

		if operator == 'starts_with':
			operator = '=ilike'
			value = value + '%'
		elif operator == 'ends_with':
			operator = '=ilike'
			value = '%' + value

		if fieldType == 'user':
			data = Rpc.session.execute('/object','execute','res.users','name_search',value)
			if data:
				value = data[0][0]
				text = data[0][1]
			else:
				value = False
				text = ''

		self.uiValue.setText( text )

		if self.isOrSelected():
			condition = '|'
		else:
			condition = '&'

		if relatedFieldName:
			queryFieldName = '%s.%s' % (fieldName, relatedFieldName)
		else:
			queryFieldName = fieldName
		return [condition,(queryFieldName, operator, value)]

	def setValue(self, domainItem):
		field = domainItem[0]
		operator = domainItem[1]
		value = domainItem[2]

		relatedField = field.split('.')[-1]
		field = field.split('.')[0]
		fieldType = self.fields[field].get('type')

		index = self.uiField.findData( QVariant( field ) )
		self.uiField.setCurrentIndex( index )

		self.updateRelatedAndOperators()

		if relatedField != field:
			fieldType = self.fields[relatedField].get('type')
			index = self.uiRelatedField.findData( QVariant( relatedField ) )
			self.uiRelatedField.setCurrentIndex( index )

		self.updateOperators()

			
		# Start with 1 because first item is empty
		i = 1
		for x in self.operators:
			if x[0] == operator and fieldType in x[2]:
				index = self.uiOperator.findData( x[0] )
				self.uiOperator.setCurrentIndex( index )
				break
			i += 1
		self.uiValue.setText( unicode(value) )	
		

class CustomSearchFormWidget(AbstractSearchWidget):
	def __init__(self, parent=None):
		AbstractSearchWidget.__init__(self, '', parent)
		
		self.layout = QVBoxLayout( self )

		self.model = None
		self.name = ''
		self.focusable = True
		self.expanded = True
		self._loaded = False
		self.fields = None
		self.widgets = []

	## @brief Returns True if it's been already loaded. That is: setup has been called.
	def isLoaded(self):
		return self._loaded

	## @brief Returns True if it has no widgets.
	def isEmpty(self):
		if len(self.widgets):
			return False
		else:
			return True

	## @brief Sets the given search item as valid or invalid
	#
	# This function is useful because several searches are not yet possible in OpenERP
	# such as some searches with property fields. This way, there's a mechanism to show
	# users that a given item search cannot be executed.
	def setItemValid(self, number, valid):
		self.widgets[number].setValid( valid )

	def setAllItemsValid(self, valid):
		for number in xrange(self.itemCount()):
			self.setItemValid(number, valid)

	def insertItem(self, previousItem=None):
		filterItem = CustomSearchItemWidget( self )
		filterItem.setup( self.fields )
		if previousItem:
			index = self.layout.indexOf(previousItem)+1
			filterItem.copyState( previousItem )
			self.layout.insertWidget( index, filterItem )
			self.widgets.insert(index, filterItem)
		else:
			self.layout.addWidget( filterItem )
			self.widgets.append( filterItem )
		self.connect( filterItem, SIGNAL('newItem()'), self.newItem )
		self.connect( filterItem, SIGNAL('removeItem()'), self.removeItem )
		return filterItem

	def dropItem(self, item, force=False):
		if len(self.widgets) > 1 or force:
			self.layout.removeWidget( item )
			item.hide()
			self.widgets.remove( item )
		else:
			item.clear()

	def newItem(self):
		self.insertItem( self.sender() )

	def removeItem(self):
		self.dropItem( self.sender() )

	def itemCount(self):
		return len(self.widgets)

	## @brief Initializes the widget with the appropiate widgets to search.
	#
	# Needed fields include XML view (usually 'form'), fields dictionary with information
	# such as names and types, and the model parameter.
	def setup(self, fields, domain):
		# We allow one setup call only
		if self._loaded:
			return 
		self._loaded = True

		self.fields = fields.copy()
		self.fields['id'] = {
			'type': 'integer',
			'string': _('( ID )'),
		}
		self.fields['create_uid'] = {
			'type': 'user',
			'string': _('( Created By )'),
		}
		self.fields['create_date'] = {
			'type': 'datetime',
			'string': _('( Creation Date )'),
		}
		self.fields['write_uid'] = {
			'type': 'user',
			'string': _('( Last Modified By )'),
		}
		self.fields['write_date'] = {
			'type': 'datetime',
			'string': _('( Last Modification Date )'),
		}
		self.insertItem()

		#for x in domain:
		#	if len(x) >= 2 and x[0] in self.widgets and x[1] == '=':
		#		self.widgets[ x[0] ].setEnabled( False )
		#for x in domain:
			#self.addItem( fields, x )
		
		#for widget in self.widgets.values():
		#	self.connect( widget, SIGNAL('keyDownPressed()'), self, SIGNAL('keyDownPressed()') )


	def setFocus(self):
		pass
		#if self.focusable:
			#self.focusable.setFocus()
		#else:
			#QWidget.setFocus(self)

	## @brief Clears all search fields.
	#
	# Calling 'value()' after this function should return an empty list.
	def clear(self, force=False):
		for item in self.widgets[:]:
			self.dropItem( item, force )
		self.setAllItemsValid(True)

	## @brief Returns a domain-like list for the current search parameters.
	#
	# Note you can optionally give a 'domain' parameter which will be added to
	# the filters the widget will return.
	def value(self, domain=[]):
		res = []
		for x in self.widgets:
			res += x.value()

		if res:
			# Remove last '&' or '|' operator
			res = res[:-2] + res[-1:]

		v_keys = [x[0] for x in res]
		for f in domain:
			if f[0] not in v_keys:
				res.append(f)
		return res

	## @brief Allows setting filter values for all fields in the form.
	#
	# 'val' parameter should be a dictionary with field names as keys and
	# field values as values. Example:
	#
	# form.setValue({
	#	'name': 'enterprise',
	#	'income': 24
	# })
	def setValue(self, domain):
		if not domain:
			self.clear()
			return
		self.clear(force=True)
		nextOr = False
		for item in domain:
			if isinstance(item, tuple):
				widgetItem = self.insertItem()
				widgetItem.setValue( item )
				if nextOr:
					widgetItem.setOrSelected()
				nextOr = False
			elif item == '|':
				nextOr = True

