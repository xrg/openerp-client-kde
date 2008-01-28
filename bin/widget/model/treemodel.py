from PyQt4.QtCore import *
from PyQt4.QtGui import *

from common import icons

#
# We store the pointer to the Tiny ModelGroup on QModelIndex.internalPointer
# Fields order should be handled using QHeaderView
#
# Qt.UserRole returns the model id (database id) for the given field (QModelIndex),
# though id() function is also provided for convenience.


## @brief The TreeModel class provides a QAbstractItemModel wrapper around 
# ModelRecordGroup class.
#
# To use this class, simply call setModelGroup() to set the ModelRecordGroup
# instance to wrap, and setFields() with the fields to load.
# Then it's ready to be used in any Qt model/view enabled widget such as 
# QTreeView or QListView.
class TreeModel(QAbstractItemModel):
	
	TreeMode = 1
	ListMode = 2

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
		# visibleFields is an alphabetically sorted list of 
		# all visible fields. This means it discards self.icon
		# and self.child fields. The list is updated using
		# updateVisibleFields().
		self.visibleFields = []
		
	## @brief Sets the ModelRecordGroup associated with this Qt Model
	#
	# Fields should already be set and can't be added after this 
	# call
	def setModelGroup(self, group):
		self.emit( SIGNAL('modelAboutToBeReset()') )
		if self.group:
			self.disconnect( self.group, SIGNAL('recordCleared()'), self.modelGroupChanged )
			self.disconnect( self.group, SIGNAL('modelChanged(PyQt_PyObject)'), self.modelChanged )
			self.disconnect( self.group, SIGNAL('recordChanged(QString,int)'), self.recordChanged )
			
		self.group = group
		if self.group:
			self.connect( self.group, SIGNAL('recordCleared()'), self.modelGroupChanged )
			self.connect( self.group, SIGNAL('modelChanged(PyQt_PyObject)'), self.modelChanged )
			self.connect( self.group, SIGNAL('recordChanged(QString,int)'), self.recordChanged )
			
		# We emit modelReset() so widgets will be notified that 
		# they need to be updated
		self.emit( SIGNAL('modelReset()') )
		self.updateVisibleFields()

	def modelGroupChanged(self):
		self.reset()
		
	def modelChanged(self,obj):
		self.reset()

	def recordChanged(self,when,pos):
		self.reset()
		
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
		#self.visibleFields = self.fields.keys()[:]
		if self.icon in self.visibleFields:
			del self.visibleFields[self.visibleFields.index(self.icon)]
		if self.child in self.visibleFields:
			del self.visibleFields[self.visibleFields.index(self.child)]
		#self.visibleFields.sort()

	## @brief Set the model to the specified mode
	#
	#  mode parameter can be TreeMode or ListMode
	def setMode(self, mode):
		self.mode = mode

	## @brief Returns the model id corresponding to index
	def id(self, index):
		if not self.group:
			return 0
		if not index.isValid():
			return 0

		model = self.model( index.row(), index.internalPointer() )
		if model:
			return model.id
		else:
			return 0

	# Pure virtual functions from QAbstractItemModel

	def rowCount(self, parent = QModelIndex()):
		if not self.group:
			return 0

		# In list mode we will consider there are no children
		if self.mode == self.ListMode and parent.internalPointer() != self.group:
			return 0

		if parent.isValid():
			# Check if this field has associated the children of another one
			field = self.field( parent.column() )
			if field == self.childField:
				fieldType = self.fieldTypeByName(self.child, parent.internalPointer())
				if fieldType == 'one2many':
					value = self.valueByName(parent.row(), self.child, parent.internalPointer())
					return len(value.models)
				elif fieldType == 'many2many':
					value = self.valueByName(parent.row(), self.child, parent.internalPointer())
					return len(value)
				else:
					return 0

			# If we get here it means tha we return the _real_ children
			fieldType = self.fieldType( parent.column(), parent.internalPointer() )
			if fieldType == 'one2many':
				value = self.value( parent.row(), parent.column(), parent.internalPointer() )
				return len(value.models)
			elif fieldType == 'many2many': 
				value = self.value( parent.row(), parent.column(), parent.internalPointer() )
				return len(value)
			else:
				return 0
		else:
			return len(self.group.models)

	def columnCount(self, parent = QModelIndex()):
		if not self.group:
			return 0

		# In list mode we consider there are no children
		if self.mode == self.ListMode and parent.internalPointer() != self.group:
			return 0

		if parent.isValid():
			#return len(parent.internalPointer().mfields)
			return len(self.visibleFields)
			fieldType = self.fieldType( parent.column(), parent.internalPointer() )
			if fieldType == 'one2many':
				# We suppose all childs have the same number of columns.
				# Note that trying to browse and search the number of fields of 
				# the model group wouldn't work we'd have to addFields() as fields
				# wouldn't be loaded. That would make the function slower.
				return len(self.visibleFields)
			elif fieldType == 'many2many':
				return len(self.visibleFields)
			else:
				return 0
		else:
			#return len(self.group.mfields)
			return len(self.visibleFields)

	def data(self, index, role):
		if not self.group:
			return QVariant()
		if role == Qt.DisplayRole:
			value = self.value( index.row(), index.column(), index.internalPointer() )
			fieldType = self.fieldType( index.column(), index.internalPointer() )
			if fieldType == 'one2many':
				return QVariant( '(%d)' % len(value.models) )
			elif fieldType == 'many2many':
				return QVariant( '(%d)' % len(value) )
			elif fieldType == 'selection':
				field = self.fields[self.field( index.column() )]
				for x in field['selection']:
					if x[0] == value:
						return QVariant( unicode(x[1]) )
				return QVariant()
			elif fieldType == 'float':
				# If we use the default conversion big numbers are shown
				# in scientific notation
				return QVariant( QString( str(value) ) )	
			else:
				if value == False or value == None:
					return QVariant()
				else:
					return QVariant( unicode(value) )
		elif role == Qt.DecorationRole:
			if self.field( index.column() ) == self.iconField:
				model = self.model( index.row(), index.internalPointer() )
				# Not all models necessarily have the icon so check that first
				if self.icon in model.values:
					return QVariant( icons.kdeIcon( model.value( self.icon ) ) )
				else:
					return QVariant()
			else:
				return QVariant()
		elif role == Qt.BackgroundRole:
			if not self.showBackgroundColor:
				return QVariant()
			field = self.fields[self.field( index.column() )]
			if 'required' in field:
				color = '#ddddff'	
			elif 'readonly' in field:
				color = 'lightgrey'
			else:
				color = 'white'
			return QVariant( QBrush( QColor( color ) ) )
		elif role == Qt.ForegroundRole:
			model = self.model( index.row(), index.internalPointer() )
			color = 'black'
			for (c, expression) in self.colors:
				if model.expr_eval( expression, check_load=False ):
					color = c
					break

			return QVariant( QBrush( QColor( color ) ) )
		elif role == Qt.UserRole:
			model = self.model( index.row(), index.internalPointer() )
			return QVariant( model.id )
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
		# Search where in the grandparent our parent is
		group = index.internalPointer()

		# We don't want to go upper the model we've been given.
		if group == self.group:
			return QModelIndex()

		# The 'parent' of the child ModelRecordGroup is a Model. The
		# model has a pointer to the ModelRecordGroup it belongs and
		# it's called 'mgroup'
		model = group.parent
		parent = group.parent.mgroup

		row = parent.models.index(model)
		for x, y in model.values.items():
			if y == group:
				field = x
				break

		# Consider childField
		if field == self.child:
			field = self.childField

		column = self.visibleFields.index(field)
		return self.createIndex( row, column, parent )	

	# Plain virtual functions from QAbstractItemModel

	def headerData(self, section, orientation, role):
		if orientation == Qt.Vertical:
			return QVariant()
		if role == Qt.DisplayRole:
			field = self.fields[ self.field( section ) ]
			return QVariant( unicode( field['string'] ) )
		else:
			return QVariant()

	## @brief Returns the field name for the given column and group
	def field(self, column):
		if column >= len(self.visibleFields):
			return None
		else:
			return self.visibleFields[column]

	## @brief Returns the field type for the given column and group
	def fieldType(self, column, group):
		field = self.field(column)
		if field:
			return group.fields[ field ]['type']
		else:
			return None

	## @brief Returns the field type for the given column and group
	def fieldTypeByName(self, field, group):
		if field in group.fields:
			return group.fields[ field ]['type']
		else:
			return None

	## @brief Returns a ModelRecord refered by row and group parameters
	def model(self, row, group):
		if row >= len(group.models):
			return None
		else:
			return group.models[row] 

	## @brief Returns the value from the model from the given row, column and group
	#
	# 'group' is usually obtained from the internalPointer() of a QModelIndex.
	def value(self, row, column, group):
		# We ensure the group has been loaded by checking if there
		# are any fields
		if not group.mfields:
			group.addFields( self.fields )
		model = self.model(row, group)
		field = self.field(column)
		if not field or not model:
			return None
		else:
			return model.value( field )

	def valueByName(self, row, field, group):
		# We ensure the group has been loaded by checking if there
		# are any fields
		if not group.mfields:
			group.addFields( self.fields )

		model = self.model( row, group )
		if not model:
			return None
		else:
			return model.value( field )

	## @brief Returns the id of the model pointed by index. 
	#
	# The index can point to any field of the model.
	def id(self, index):
		model = self.model( index.row(), index.internalPointer() )
		if model:
			return model.id
		else:
			return -1

	## @brief Returns a QModelIndex pointing to the first field of a given 
	# a model id
	def indexFromId(self, id):
		if not self.group:
			return QModelIndex()

		i = 0
		for x in self.group.models:
			if x.id == id:
				return self.index( i, 0 )
			i = i + 1
		return QModelIndex()

