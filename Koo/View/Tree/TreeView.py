##############################################################################
#
# Copyright (c) 2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
# Copyright (c) 2007 Angel Alvarez <angel@nan-tic.com>
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

from Koo.Model import KooModel
from Koo.Model.Group import RecordGroup
from Koo.View.AbstractView import *
from Koo.Fields.AbstractFieldDelegate import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from Koo.Common import Numeric
from Koo import Rpc

class KooTreeView(QTreeView):
	def contextMenuEvent( self, event ):
		index = self.indexAt( event.pos() )
		delegate = self.itemDelegate( index )
		if not isinstance(delegate, AbstractFieldDelegate):
			return
		delegate.showPopupMenu( self, self.mapToGlobal( event.pos() ) )

	def sizeHintForColumn( self, column ):
		QApplication.setOverrideCursor( Qt.WaitCursor )
		try:
			model = self.model()
			# We expect a KooModel here!
			group = model.recordGroup()
			records = group.loadedRecords()
			# If all records are loaded it's faster to use the C++ implementation
			if len(records) == group.count():
				QApplication.restoreOverrideCursor()
				return QTreeView.sizeHintForColumn( self, column )
			viewOptions = self.viewOptions()
			delegate = self.itemDelegateForColumn( column )
			hint = 0
			for record in records:
				index = model.indexFromRecord( record )
				index = model.index( index.row(), column, index.parent() )
				hint = max( hint, delegate.sizeHint( viewOptions, index ).width() )
		except Rpc.RpcException, e:
			hint = 100
		QApplication.restoreOverrideCursor()
		return hint

	def moveCursor(	self, action, modifiers ):
		index = self.currentIndex()
		if not index.isValid():
			return QModelIndex()
		row = index.row()
		column = index.column()
		lastRow = index.model().rowCount() - 1
		lastColumn = index.model().columnCount() - 1
		if action == QAbstractItemView.MoveUp:
			row -= 1
		elif action == QAbstractItemView.MoveDown:
			row += 1
		elif action == QAbstractItemView.MoveLeft:
			column -= 1
		elif action == QAbstractItemView.MoveRight:
			column += 1
		elif action == QAbstractItemView.MoveHome:
			if column == 0:
				row = 0
			else:
				column = 0 
		elif action == QAbstractItemView.MoveEnd:
			if column == lastColumn:
				row = lastRow
			else:
				column = lastColumn
		elif action == QAbstractItemView.MovePageUp:
			row -= 12 
		elif action == QAbstractItemView.MovePageDown:
			row += 12 
		elif action == QAbstractItemView.MoveNext:
			column += 1
		elif action == QAbstractItemView.MovePrevious:
			column -= 1

		if column > lastColumn:
			column = 0
			row += 1
		elif column < 0:
			column = lastColumn
			row -= 1
		if row < 0:
			column = 0
			row = 0
		elif row > lastRow:
			row = lastRow
			column = 0
		return self.model().createIndex( row, column, index.internalPointer() ) 

class TreeView( AbstractView ):

	def __init__(self, parent, widgetType='tree'):
		AbstractView.__init__(self, parent)
		self._widgetType = widgetType
		self.treeModel = None
		self.reload = False
		self.title=""
		self.selecting = False
		self.setAddOnTop( False )

		if self._widgetType == 'tree':
			self.widget = KooTreeView( self )
			self.widget.setAllColumnsShowFocus( False )
			self.widget.setSortingEnabled(True)
			self.widget.setRootIsDecorated( False )
			self.widget.setAlternatingRowColors( True )
			self.widget.setVerticalScrollMode( QAbstractItemView.ScrollPerItem )
			self.widget.sortByColumn( 0, Qt.AscendingOrder )
			self.widget.setDragEnabled( True )
			self.widget.setAcceptDrops( True )
			self.widget.setDropIndicatorShown( True );
			self.widget.setDragDropMode( QAbstractItemView.InternalMove )

			# We set uniformRowHeights property to True because this allows some 
			# optimizations. It makes a really big difference in models with thousands 
			# of tuples because moving to the end of the list only requires to query
			# for those items at the end (those that are shown) wheras if we don't
			# guarantee that all items have the same height, all previous items
			# need to be loaded too so the view can measure what height they are
			# and in which position the scroll is.
			self.widget.setUniformRowHeights( True )
		elif self._widgetType == 'list':
			self.widget = QListView( self )
			self.widget.setViewMode( QListView.IconMode )
			self.widget.setFlow( QListView.LeftToRight )
			self.widget.setGridSize( QSize( 200, 20 ) )
			self.widget.setResizeMode( QListView.Adjust )
		elif self._widgetType == 'table':
			self._widgetType = 'table'
			self.widget = QTableView( self )

		# Set focus proxy so other widgets can try to setFocus to us
		# and the focus is set to the expected widget.
		self.setFocusProxy( self.widget )

		# Contains list of aggregated fields
		self.aggregates = []
		self.aggregatesContainer = QWidget( self )
		self.aggregatesLayout = QHBoxLayout( self.aggregatesContainer )
		self.aggregatesLayout.setContentsMargins( 0, 0, 0, 0 )

		self.setAllowMultipleSelection(True)

		self.connect( self.widget, SIGNAL('activated(QModelIndex)'), self.activated )

		self.currentRecord = None

		layout = QVBoxLayout()
		layout.setContentsMargins(0, 0, 0, 0)
		layout.addWidget( self.widget )
		layout.addWidget( self.aggregatesContainer )
		self.setLayout( layout )
		self._readOnly = True

	def sizeHint(self):
		return QSize(10, 10)
	
	def viewType(self):
		return 'tree'

	def setGridWidth( self, width ):
		if self._widgetType == 'list':
			self.widget.setGridSize( QSize( width, self.widget.gridSize().height() ) )

	def setGridHeight( self, height ):
		if self._widgetType == 'list':
			self.widget.setGridSize( QSize( self.widget.gridSize().width(), height ) )

	def setModel( self, model ):
		self.currentRecord = None
		self.treeModel = model	
		self.widget.setModel( self.treeModel )
		self.connect( self.widget.selectionModel(),SIGNAL('currentChanged(QModelIndex, QModelIndex)'),self.currentChanged)
		self.connect( self.treeModel, SIGNAL('rowsInserted(const QModelIndex &,int,int)'), self.updateAggregates )
		self.connect( self.treeModel, SIGNAL('rowsRemoved(const QModelIndex &,int,int)'), self.updateAggregates )
		self.connect( self.treeModel, SIGNAL('modelReset()'), self.updateAggregates )
		self.connect( self.treeModel.recordGroup(), SIGNAL('sorting'), self.sorting )

	def sorting(self, value):
		if value == RecordGroup.SortingNotPossible:
			self.emit( SIGNAL('statusMessage(QString)'), _("<font color='red'>Sorting not possible.</font>") )
		elif value == RecordGroup.SortingOnlyGroups:
			self.emit( SIGNAL('statusMessage(QString)'), _("<font color='red'>Sorting only groups.</font>") )
		elif value == RecordGroup.SortingNotPossibleModified:
			self.emit( SIGNAL('statusMessage(QString)'), _("<font color='red'>Save changes before sorting.</font>") )
		else:
			self.emit( SIGNAL('statusMessage(QString)'), '' )

	def addAggregate( self, name, label, bold, digits ):
		aggLabel = QLabel( label + ':', self.aggregatesContainer )
		aggLabel.setSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed )
		aggValue = QLabel( self.aggregatesContainer )
		aggValue.setSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed )
		if bold:
			font = QFont()
			font.setBold( True )
			aggLabel.setFont( font )
			aggValue.setFont( font )
		self.aggregatesLayout.addWidget( aggLabel )
		self.aggregatesLayout.addWidget( aggValue )
		self.aggregatesLayout.addSpacing( 10 )
		self.aggregates.append( { 'name': name, 'widget': aggValue, 'digits': digits } )

	def finishAggregates(self):
		self.aggregatesLayout.addSpacing( 10 )
		# The uiUpdateAggregates QLabel will be shown only when not all records are loaded in the record group.
		# In such a case, aggregates are not calculated and the user must clic the link in the label in order
		# to see aggregates calculated.
		self.uiUpdateAggregates = QLabel( _('<a href="update">Update totals</a>'), self.aggregatesContainer )
		self.uiUpdateAggregates.setSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed )
		self.connect( self.uiUpdateAggregates, SIGNAL('linkActivated(QString)'), self.forceAggregatesUpdate )
		self.aggregatesLayout.addWidget( self.uiUpdateAggregates )
		self.aggregatesLayout.addStretch( 0 )

	## @brief Forces calculation of aggregates, even if not all records in the group have been loaded yet.
	def forceAggregatesUpdate(self, url):
		QApplication.setOverrideCursor( Qt.WaitCursor )
		try:
			self.treeModel.group.ensureAllLoaded()
			self.updateAggregates()
		except Rpc.RpcException, e:
			pass
		QApplication.restoreOverrideCursor()

	# This signal is emited when a list item is double clicked
	# or activated, only when it's read-only.
	# Used by the search dialog to "accept" the choice or by
	# Screen to switch view
	def activated(self, index):
		if self._readOnly:
			import logging
			log = logging.getLogger('koo.treeview')
			log.debug('activated(%s)', str(index))
			self.emit( SIGNAL('activated()') )
			log.debug('finish activated()')

	def currentChanged(self, current, previous):
		if self.selecting:
			return
		self.currentRecord = self.treeModel.recordFromIndex( current )
		# We send the current record. Previously we sent only the id of the model, but
		# new models have id=None
		self.emit( SIGNAL("currentChanged(PyQt_PyObject)"), self.currentRecord )
		self.updateAggregates()

	def store(self):
		# Ensure current editor is stored before saving:
		# As closing the current editor doesn't store the info in the model
		# we need to open a new one (so the old is closed smartly) and then
		# close it again.
		# We must close it again because we don't know if there was an editor.
		self.widget.openPersistentEditor( self.widget.currentIndex() )
		self.widget.closePersistentEditor( self.widget.currentIndex() )

	def reset(self):
		pass

	def setSelected(self, record):
		if self.currentRecord == record:
			return
		self.currentRecord = record
		idx = self.treeModel.indexFromRecord( record )
		if idx != None:
			self.selecting = True
			self.widget.selectionModel().setCurrentIndex( idx, QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)
			self.selecting = False

	def display(self, currentRecord, recordGroup ):
		# TODO: Avoid setting the model group each time...
		self.treeModel.setRecordGroup( recordGroup )
		if self._widgetType != 'tree':
			self.treeModel.sort( 0, Qt.AscendingOrder )
		self.updateAggregates()
		if currentRecord:
			idx = self.treeModel.indexFromRecord( currentRecord )
			if idx:
				self.widget.setCurrentIndex( idx )
				self.widget.selectionModel().select( self.widget.currentIndex(), QItemSelectionModel.SelectCurrent | QItemSelectionModel.Rows )

	## @brief Selects the first item of the list.
	def selectFirst(self):
		index = self.treeModel.index( 0, 0 )
		if not index.isValid():
			return
		self.widget.setCurrentIndex( index )
		self.widget.selectionModel().select( self.widget.currentIndex(), QItemSelectionModel.SelectCurrent | QItemSelectionModel.Rows )

	## @brief Selects all items of the list.
	def selectAll(self):
		start = self.treeModel.index( 0, 0 )
		end = self.treeModel.index( self.treeModel.rowCount() - 1, 0 )
		# We call selectFirst() before setting the selection because we want to ensure that 
		# "self.currenRecord" is set. Otherwise we're selecting all records without keeping
		# track that the current selected item is the first one, and when we receive the
		# next call to setSelected() from Screen, we're updating the selection and only the
		# first item is selected.
		self.selectFirst()
		selection = QItemSelection( start, end )
		self.widget.selectionModel().select( selection, QItemSelectionModel.SelectCurrent | QItemSelectionModel.Rows )

	def selectedRecords(self):
		records = []
		selectedIndexes = self.widget.selectionModel().selectedRows()
		for i in selectedIndexes:
			record = self.treeModel.recordFromIndex( i )
			# Qt always returns at least one selected row (probably it's the root)
			# so we need to check that record!=None
			if record:
				records.append( self.treeModel.recordFromIndex( i ) )
		return records

	def setAllowMultipleSelection(self, value):
		if value:
			self.widget.setSelectionMode( QAbstractItemView.ExtendedSelection )
		else:
			self.widget.setSelectionMode( QAbstractItemView.SingleSelection )

	def setReadOnly(self, value):
		# We only allow readOnly property to be set if recordGroup is read-write.
		if not self.treeModel:
			return
		if self.treeModel.isReadOnly():
			return
		self._readOnly = value
		if self._readOnly:
			self.widget.setEditTriggers( QAbstractItemView.NoEditTriggers ) 
			self.widget.setTabKeyNavigation( False )
		else:
			self.widget.setEditTriggers( QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed | QAbstractItemView.AnyKeyPressed | QAbstractItemView.SelectedClicked )
			# Allow tab navigation because otherwise non editable fields
			# make tab go out of the widget when editting.
			self.widget.setTabKeyNavigation( True )
	
	def isReadOnly(self):
		return self._readOnly

	## @brief Updates aggregates values. Note that if some records have not been loaded it 
	# will show a hyphen instead of the appropiate value, avoiding long load times for some
	# screens.
	def updateAggregates(self):
		if self.treeModel.group and self.aggregates:
			if self.treeModel.group.unloadedIds():
				self.uiUpdateAggregates.show()
				calculate = False
			else:
				self.uiUpdateAggregates.hide()
				calculate = True
		else:
			calculate = False
			self.uiUpdateAggregates.hide()

		for agg in self.aggregates:
			# As we don't want the aggregates to force loading all records
			# don't calculate aggregates if there are unloaded records.
			if calculate:
				value = 0.0
				for model in self.treeModel.group:
					value += model.value(agg['name'])
				agg['widget'].setText( Numeric.floatToText( value, agg['digits'] ) )
			else:
				agg['widget'].setText( '-' )

	def startEditing(self):
		self.widget.edit( self.widget.currentIndex() )

	def addOnTop(self):
		return self._addOnTop

	def setAddOnTop(self, add):
		self._addOnTop = add

	def viewSettings(self):
		if self._widgetType in ('list','table'):
			return ''
		header = self.widget.header()
		return str( header.saveState().toBase64() )

	def setViewSettings(self, settings):
		if not settings or self._widgetType in ('list','table'):
			return
		header = self.widget.header()
		header.restoreState( QByteArray.fromBase64( settings ) )

