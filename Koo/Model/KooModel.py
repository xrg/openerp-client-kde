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

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from Koo.Common import Icons
from Koo.Common import Calendar
from Koo.Common import Numeric
from Koo.Common import Common

#
# We store the pointer to the Tiny ModelGroup on QModelIndex.internalPointer
# Fields order should be handled using QHeaderView
#
# Qt.UserRole returns the model id (database id) for the given field (QModelIndex),
# though id() function is also provided for convenience.


## @brief The KooModel class provides a QAbstractItemModel wrapper around 
# RecordGroup class.
#
# To use this class, simply call setRecordGroup() to set the RecordGroup
# instance to wrap, and setFields() with the fields to load.
# Then it's ready to be used in any Qt model/view enabled widget such as 
# QTreeView or QListView.
# Note that by default KooModel is read-only.
class KooModel(QAbstractItemModel):
	
	# Modes
	TreeMode = 1
	ListMode = 2

	# Extra roles appended to UserRole
	
	# IdRole: Returns model id of the given field
	IdRole = Qt.UserRole 
	# ValueRole: Returns the QVariant of the appropiate type
	# for the field. For example, date fields are returned as
	# QDate inside QVariant, instead of a QString as Qt.DisplayRole
	# does. It's been created for the Calendar view but others
	# might benefit too.
	ValueRole = Qt.UserRole + 1 

	def __init__(self, parent=None):
		QAbstractItemModel.__init__(self, parent)
		self.group = None
		self.fields = {}
		self.icon = ''
		self.iconField = ''
		self.child = ''
		self.childField = ''
		self.mode = self.TreeMode
		self.colors = {}
		self.showBackgroundColor = True
		self._readOnly = True
		self._updatesEnabled = True
		# visibleFields is an alphabetically sorted list of 
		# all visible fields. This means it discards self.icon
		# and self.child fields. The list is updated using
		# updateVisibleFields().
		self.visibleFields = []
		
	## @brief Sets the RecordGroup associated with this Qt Model
	#
	# Fields should already be set and can't be added after this 
	# call
	def setRecordGroup(self, group):
		self.emit( SIGNAL('modelAboutToBeReset()') )
		if self.group:
			self.disconnect( self.group, SIGNAL('recordsInserted(int,int)'), self.recordsInserted )
			self.disconnect( self.group, SIGNAL('recordChanged(PyQt_PyObject)'), self.recordChanged )
			self.disconnect( self.group, SIGNAL('recordsRemoved(int,int)'), self.recordsRemoved )
			
		self.group = group
		if self.group:
			self.connect( self.group, SIGNAL('recordsInserted(int,int)'), self.recordsInserted )
			self.connect( self.group, SIGNAL('recordChanged(PyQt_PyObject)'), self.recordChanged )
			self.connect( self.group, SIGNAL('recordsRemoved(int,int)'), self.recordsRemoved )
			
		# We emit modelReset() so widgets will be notified that 
		# they need to be updated
		self.emit( SIGNAL('modelReset()') )
		self.updateVisibleFields()

	## @brief Returns the current RecordGroup associated with this Qt Model
	def recordGroup(self):
		return self.group

	## @brief Sets the model as read-only.
	def setReadOnly(self, value):
		self._readOnly = value

	## @brief Returns whether the model is read-only or read-write.
	def readOnly(self):
		return self._readOnly

	def recordsInserted(self, start, end):
		if self._updatesEnabled:
			self.reset()
			#self.emit( SIGNAL('rowsAboutToBeInserted(QModelIndex,int,int)'), QModelIndex(), start, end ) 
			#self.emit( SIGNAL('rowsInserted(QModelIndex,int,int)'), QModelIndex(), start, end ) 

	def recordChanged(self, record):
		if not record:
			return
		leftIndex = self.indexFromId( record.id )
		if not leftIndex.isValid():
			self.reset()
			return
		rightIndex = self.index( leftIndex.row(), self.columnCount() - 1 )
		self.emit( SIGNAL('dataChanged(QModelIndex,QModelIndex)'), leftIndex, rightIndex )

	def recordsRemoved(self, start, end):
		if self._updatesEnabled:
			self.reset()
			#self.emit( SIGNAL('rowsAboutToBeRemoved(QModelIndex,int,int)'), QModelIndex(), start, end ) 
			#self.emit( SIGNAL('rowsRemoved(QModelIndex,int,int)'), QModelIndex(), start, end ) 
		
	## @brief Sets the dictionary of fields that should be loaded
	def setFields(self, fields):
		self.fields = fields
		self.updateVisibleFields()

	## @brief Sets the order in which fields should be put in the model.
	#
	# If this function is never called fields are put in alphabetical
	# order.
	def setFieldsOrder(self, fields):
		self.visibleFields = fields
		self.updateVisibleFields()

	## @brief Sets the dictionary of colors
	#
	# The dictionary is of the form 'color' : 'expression', where 
	# 'expression' is a python boolean expression that will be passed
	# to the model, and thus can use model context information.
	def setColors(self, colors):
		self.colors = colors

	## @brief Sets whether the background color should be returned in 
	# data() or not.
	#
	# Setting this to True (default) will make the call to data() with 
	# Qt.BackgroundRole to return the appropiate background color 
	# if fields are read only or required.
	def setShowBackgroundColor(self, showBackgroundColor):
		self.showBackgroundColor = showBackgroundColor

	## @brief Sets that the contents of field 'icon' are used as an icon
	# for field 'iconField'
	#
	# The contents (usually an icon name) of the field 'icon' is used for
	# the decoration role of 'iconField'
	def setIconForField(self, icon, iconField):
		self.icon = icon
		self.iconField = iconField
		self.updateVisibleFields()

	## @brief Sets that the children of field 'child' are used as an children 
	# for field 'childField'
	def setChildrenForField(self, child, childField):
		self.child = child
		self.childField = childField
		self.updateVisibleFields()

	# Updates the list of visible fields. The list is kept sorted and icon
	# and child fields are excluded if they have been specified.
	def updateVisibleFields(self):
		if not self.visibleFields:
			self.visibleFields = self.fields.keys()[:]
		if self.icon in self.visibleFields:
			del self.visibleFields[self.visibleFields.index(self.icon)]
		if self.child in self.visibleFields:
			del self.visibleFields[self.visibleFields.index(self.child)]

	## @brief Set the model to the specified mode
	#
	# mode parameter can be TreeMode or ListMode, this is not %100
	# necessary in most cases, but it also avoids some checks in many cases
	# so at least it can provide some speed improvements.
	def setMode(self, mode):
		self.mode = mode

	## @brief Returns the model id corresponding to index
	def id(self, index):
		if not self.group:
			return 0
		if not index.isValid():
			return 0

		model = self.record( index.row(), index.internalPointer() )
		if model:
			return model.id
		else:
			return 0

	# Pure virtual functions from QAbstractItemModel

	def rowCount(self, parent = QModelIndex()):
		if not self.group:
			return 0

		# In list mode we will consider there are no children
		if self.mode == self.ListMode and parent.isValid() and parent.internalPointer() != self.group:
			return 0

		if parent.isValid():
			# Check if this field has associated the children of another one
			field = self.field( parent.column() )
			if field == self.childField:
				fieldType = self.fieldTypeByName(self.child, parent.internalPointer())
				if fieldType in ['one2many', 'many2many']:
					value = self.valueByName(parent.row(), self.child, parent.internalPointer())
					if value:
						return value.count()
					else:
						return 0
				else:
					return 0

			# If we get here it means that we return the _real_ children
			fieldType = self.fieldType( parent.column(), parent.internalPointer() )
			if fieldType in ['one2many', 'many2many']:
				value = self.value( parent.row(), parent.column(), parent.internalPointer() )
				return value.count()
			else:
				return 0
		else:
			return self.group.count()

	def columnCount(self, parent = QModelIndex()):
		if not self.group:
			return 0

		# In list mode we consider there are no children
		if self.mode == self.ListMode and parent.isValid() and parent.internalPointer() != self.group:
			return 0

		# We always return all visibleFields. If the element should have no children then no
		# rows will be returned. This way we avoid duplication of calculations.
		return len(self.visibleFields)

	def flags(self, index):
		defaultFlags = QAbstractItemModel.flags(self, index)
		if 'sequence' in self.fields:
			defaultFlags = defaultFlags | Qt.ItemIsDropEnabled
			if index.isValid():
				defaultFlags = defaultFlags | Qt.ItemIsDragEnabled

		field = self.fields[self.field( index.column() )]
		if self._readOnly or ( 'readonly' in field and field['readonly'] ):
			return defaultFlags
		else:
			return defaultFlags | Qt.ItemIsEditable

	def setData(self, index, value, role):

		if role != Qt.EditRole:
			return True
		if not index.isValid():
			return True
		model = self.record( index.row(), index.internalPointer() )
		if not model:
			return True
		field = self.field( index.column() )
		fieldType = self.fieldType( index.column(), index.internalPointer() )

		if fieldType == 'boolean':
			model.setValue( field, value.toBool() )
		elif fieldType in ('float', 'float_time'):
			model.setValue( field, value.toDouble()[0] )
		elif fieldType == 'integer':
			model.setValue( field, value.toInt()[0] )
		elif fieldType == 'selection':
			value = unicode( value.toString() )
			modelField = self.fields[self.field( index.column() )]
			for x in modelField['selection']:
				if x[1] == value:
					model.setValue( field, x[0] )
		elif fieldType in ('char', 'text'):
			model.setValue( field, unicode( value.toString() ) )
		elif fieldType == 'date':
			model.setValue( field, Calendar.dateToStorage( value.toDate() ) )
		elif fieldType == 'datetime' and value:
			model.setValue( field, Calendar.dateTimeToStorage( value.toDateTime() ) )
		elif fieldType == 'time' and value:
			model.setValue( field, Calendar.timeToStorage( value.toTime() ) )
		elif fieldType == 'many2many':
			m = model.value( field )
			m.clear()
			ids = [x.toInt()[0] for x in value.toList()]
			m.load( ids )
		elif fieldType == 'many2one':
			value = value.toList()
			if value:
				value = [ int(value[0].toInt()[0]), unicode(value[1].toString()) ]
			model.setValue( field, value )
		else:
			print "Unable to store value of type: ", fieldType

		return True

	def data(self, index, role=Qt.DisplayRole ):
		if not self.group:
			return QVariant()
		if role == Qt.DisplayRole or role == Qt.EditRole:
			value = self.value( index.row(), index.column(), index.internalPointer() )
			fieldType = self.fieldType( index.column(), index.internalPointer() )
			if fieldType in ['one2many', 'many2many']:
				return QVariant( '(%d)' % value.count() )
			elif fieldType == 'selection':
				field = self.fields[self.field( index.column() )]
				for x in field['selection']:
					if x[0] == value:
						return QVariant( unicode(x[1]) )
				return QVariant()
			elif fieldType == 'date' and value:
				return QVariant( Calendar.dateToText( Calendar.storageToDate( value ) ) )
			elif fieldType == 'datetime' and value:
				return QVariant( Calendar.dateTimeToText( Calendar.storageToDateTime( value ) ) )
			elif fieldType == 'float':
				# If we use the default conversion big numbers are shown
				# in scientific notation. Also we have to respect the number
				# of decimal digits given by the server.
				field = self.fields[self.field( index.column() )]
				return QVariant( Numeric.floatToText(value, field.get('digits',None) ) )	
			elif fieldType == 'integer':
				return QVariant( Numeric.integerToText(value) )	
			elif fieldType == 'float_time':
				return QVariant( Calendar.floatTimeToText(value) )
			elif fieldType == 'binary':
				if value:
					return QVariant( _('%d bytes') % len(value) )
				else:
					return QVariant()
			elif fieldType == 'boolean':
				return QVariant( bool(value) )
			else:
				if value == False or value == None:
					return QVariant()
				else:
					# If the text has several lines put them all in a single one
					return QVariant( unicode(value).replace('\n', ' ') )
		elif role == Qt.DecorationRole:
			if self.field( index.column() ) == self.iconField:
				model = self.record( index.row(), index.internalPointer() )
				# Not all models necessarily have the icon so check that first
				if model and self.icon in model.values:
					return QVariant( Icons.kdeIcon( model.value( self.icon ) ) )
				else:
					return QVariant()
			else:
				return QVariant()
		elif role == Qt.BackgroundRole:
			if not self.showBackgroundColor:
				return QVariant()
			field = self.fields[self.field( index.column() )]
			model = self.record( index.row(), index.internalPointer() )
			# We need to ensure we're not being asked about a non existent row.
			# This happens in some special cases (an editable tree in a one2many field,
			# such as the case of fiscal year inside sequences).
			# Note that trying to avoid processing this function if index.row() > self.rowCount()-1 
			# works to avoid this but has problems with some tree structures (such as the menu).
			# So we need to make the check here.
			if not model:
				return QVariant()
			# Priorize readonly to required as if it's readonly the 
			# user doesn't mind if it's required as she won't be able
			# to change it anyway.
			if not model.isFieldValid( self.field( index.column() ) ):
				color = '#FF6969'
			elif 'readonly' in field and field['readonly']:
				color = 'lightgrey'
			elif 'required' in field and field['required']:
				color = '#ddddff'	
			else:
				color = 'white'
			return QVariant( QBrush( QColor( color ) ) )
		elif role == Qt.ForegroundRole:
			if not self.colors:
				return QVariant()
			model = self.record( index.row(), index.internalPointer() )
			# We need to ensure we're not being asked about a non existent row.
			# This happens in some special cases (an editable tree in a one2many field,
			# such as the case of fiscal year inside sequences).
			# Note that trying to avoid processing this function if index.row() > self.rowCount()-1 
			# works to avoid this but has problems with some tree structures (such as the menu).
			# So we need to make the check here.
			if not model:
				return QVariant()
			palette = QPalette()
			color = palette.color( QPalette.WindowText )
			for (c, expression) in self.colors:
				if model.evaluateExpression( expression, checkLoad=False ):
					color = c
					break
			return QVariant( QBrush( QColor( color ) ) )
		elif role == Qt.TextAlignmentRole:
			fieldType = self.fieldType( index.column(), index.internalPointer() )
			if fieldType in ['integer', 'float', 'float_time', 'time', 'date', 'datetime']:
				return QVariant( Qt.AlignRight | Qt.AlignVCenter )
			else:
				return QVariant( Qt.AlignLeft | Qt.AlignVCenter )
		elif role == KooModel.IdRole:
			model = self.record( index.row(), index.internalPointer() )
			return QVariant( model.id )
		elif role == KooModel.ValueRole:
			value = self.value( index.row(), index.column(), index.internalPointer() )
			fieldType = self.fieldType( index.column(), index.internalPointer() )
			if fieldType in ['one2many', 'many2many']:
				# By now, return the same as DisplayRole for these
				return QVariant( '(%d)' % value.count() )
			elif fieldType == 'selection':
				# By now, return the same as DisplayRole for these
				field = self.fields[self.field( index.column() )]
				for x in field['selection']:
					if x[0] == value:
						return QVariant( unicode(x[1]) )
				return QVariant()
			elif fieldType == 'date' and value:
				return QVariant( Calendar.storageToDate( value ) )
			elif fieldType == 'datetime' and value:
				return QVariant( Calendar.storageToDateTime( value ) )
			elif fieldType == 'float':
				# If we use the default conversion big numbers are shown
				# in scientific notation. Also we have to respect the number
				# of decimal digits given by the server.
				field = self.fields[self.field( index.column() )]
				return QVariant( Numeric.floatToText(value, field.get('digits',None) ) )	
			elif fieldType == 'float_time':
				return QVariant( value )
			elif fieldType == 'binary':
				if value:
					return QVariant( QByteArray.fromBase64( value ) )
				else:
					return QVariant()
			elif fieldType == 'boolean':
				return QVariant( bool(value) )
			else:
				if value == False or value == None:
					return QVariant()
				else:
					return QVariant( unicode(value) )
		else:
			return QVariant()

	def index(self, row, column, parent = QModelIndex() ):
		if not self.group:
			return QModelIndex()
		if parent.isValid():
			# Consider childField
			field = self.field( parent.column() )
			if field == self.childField:
				field = self.child

			value = self.valueByName( parent.row(), field, parent.internalPointer() )
			return self.createIndex( row, column, value )
		else:
			return self.createIndex( row, column, self.group )

	def parent(self, index):
		if not self.group:
			return QModelIndex()
		if not index.isValid():
			return QModelIndex()
		if self.mode == self.ListMode:
			return QModelIndex()

		# Search where in the grandparent our parent is
		group = index.internalPointer()

		# We don't want to go upper the model we've been given.
		if group == self.group:
			return QModelIndex()

		# The 'parent' of the child RecordGroup is a Model. The
		# model has a pointer to the RecordGroup it belongs and
		# it's called 'group'
		model = group.parent
		parent = group.parent.group

		if not parent.recordExists( model ):
			# Though it should not normally happen, when you reload 
			# in the main menu we receive calls in which the model
			# is not in the list.
			return QModelIndex()

		row = parent.indexOfRecord( model )
		for x, y in model.values.items():
			if y == group:
				field = x
				break

		# Consider childField
		if field == self.child:
			field = self.childField

		# We check if the field is in the visibleFields. This can happen
		# if the user forgot to set ListMode and there are children (or parents)
		# of different types, so related models don't have the same
		# fields. This crashed when browsing with the form view, but could
		# happen in other places too.
		if field in self.visibleFields:
			column = self.visibleFields.index(field)
			return self.createIndex( row, column, parent )	
		else:
			return QModelIndex()

	def mimeTypes(self):
		return QStringList( [ 'text/plain' ] )

	def mimeData(self, indexes):
		data = QMimeData()
		d = []
		for index in indexes:
			if index.column() == 0:
				d.append( self.id( index ) )
		data.setText( str( d[0] ) )
		return data

	def dropMimeData(self, data, action, row, column, parent):
		if action != Qt.MoveAction:
			return False
		if not parent.isValid():
			return False
		if row != -1 or column != -1:
			return False
		group = parent.internalPointer()
		# Change record order only if the group is sorted by 'sequence' field.
		# Otherwise don't even try to move it as group.sort() won't work due to
		# the need to call the server and thus it'd lose changes.
		# By now, when sortedField is None we consider as if it was 'sequence'
		# because most views will have it as default sort field.
		if group.sortedField and group.sortedField != 'sequence':
			return False
		record = self.recordFromIndex( parent )
		seq = record.value( 'sequence' )
		seq = seq or 0
		if group.sortedOrder == Qt.AscendingOrder:
			seq += 1
		else:
			seq -= 1

		id = int( str( data.text() ) )
		movedRecord = self.recordFromIndex( self.indexFromId( id ) )
		movedRecord.setValue( 'sequence', seq )
		group.records.remove( movedRecord )
		group.records.insert( group.records.index(record), movedRecord )
		self.reset()
		return True

	def supportedDropActions(self):
		return Qt.CopyAction | Qt.MoveAction

	# Plain virtual functions from QAbstractItemModel

	def sort(self, column, order):
		QApplication.setOverrideCursor( Qt.WaitCursor )
		try:
			self.group.sort( self.field( column ), order )
		except Rpc.RpcException, e:
			pass
		QApplication.restoreOverrideCursor()

	def headerData(self, section, orientation, role):
		if orientation == Qt.Vertical:
			return QVariant()
		if role == Qt.DisplayRole:
			field = self.fields[ self.field( section ) ]
			return QVariant( Common.normalizeLabel( unicode( field['string'] ) ) )
		elif role == Qt.FontRole and not self._readOnly:
			if self.group.isFieldRequired( self.field( section ) ):
				font = QFont()
				font.setBold( True )
				return QVariant( font )
		return QVariant()

	## @brief Returns the field name for the given column 
	def field(self, column):
		if column >= len(self.visibleFields):
			return None
		else:
			return self.visibleFields[column]

	# Note that in both fieldType() and fieldTypeByName() functions we ignore 
	# the 'group' parameter and use 'self.group' instead as this improves performance
	# as in some cases we won't force loading a record just to know a field type.

	## @brief Returns the field type for the given column and group
	def fieldType(self, column, group):
		field = self.field(column)
		if field:
			return self.group.fields[ field ]['type']
		else:
			return None

	## @brief Returns the field type for the given column and group
	def fieldTypeByName(self, field, group):
		if field in self.group.fields:
			return self.group.fields[ field ]['type']
		else:
			return None

	## @brief Returns a Record refered by row and group parameters
	def record(self, row, group):
		if not group:
			return None
		# We ensure the group has been loaded by checking if there
		# are any fields. modelByIndex loads on demand, but it means
		# two reads to the server. So with these two lines (addFields)
		# we only have performance gains they can be removed with 
		# the only drawback that the server will be queried twice.
		if not group.fields:
			group.addFields( self.fields )
		if row >= group.count():
			return None
		else:
			return group.modelByIndex( row )

	## @brief Returns the value from the model from the given row, column and group
	#
	# 'group' is usually obtained from the internalPointer() of a QModelIndex.
	def value(self, row, column, group):
		# We ensure the group has been loaded by checking if there
		# are any fields
		if not group.fields:
			group.addFields( self.fields )
		model = self.record(row, group)
		field = self.field(column)
		if not field or not model:
			return None
		else:
			return model.value( field )

	def setValue(self, value, row, column, group):
		# We ensure the group has been loaded by checking if there
		# are any fields
		if not group.fields:
			group.addFields( self.fields )
		model = self.record(row, group)
		field = self.field(column)
		if field and model:
			model.setValue( field, value )
		

	def valueByName(self, row, field, group):
		# We ensure the group has been loaded by checking if there
		# are any fields
		if not group.fields:
			group.addFields( self.fields )

		model = self.record( row, group )
		if not model:
			return None
		else:
			return model.value( field )

	## @brief Returns the id of the model pointed by index. 
	#
	# The index can point to any field of the model.
	def id(self, index):
		model = self.record( index.row(), index.internalPointer() )
		if model:
			return model.id
		else:
			return -1

	## @brief Returns a QModelIndex pointing to the first field of a given 
	# a model id
	def indexFromId(self, id):
		if not self.group:
			return QModelIndex()

		row = self.group.indexOfId( id )
		if row >= 0:
			return self.index( row, 0 )
		return QModelIndex()

	def recordFromIndex(self, index):
		return self.record( index.row(), index.internalPointer() )
