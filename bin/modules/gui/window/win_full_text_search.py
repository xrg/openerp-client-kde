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

import gettext
from common import common

import rpc

from widget.screen import Screen
import widget_search

import gc
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.uic import *

class SearchViewItem( QWidget ):
	def __init__( self, uiFile, parent = None ):
		QWidget.__init__( self, parent )
		loadUi( uiFile, self )
		self.index = None

## @brief The SearchView class provides a view for a list of custom widgets.
#
# SearchView, simplifies the task of creating a list-like view for a model
# in which the items of the list are custom widgets. Even more, SearchView
# allows to trivially use a '.ui' to be used as items, where you only need
# to map model indexes into .ui widget names.
class SearchView( QAbstractItemView ):
	def __init__( self, parent = None ):
		QAbstractItemView.__init__( self, parent )
		self.setViewport( QWidget(self) )
		layout = QVBoxLayout( self.viewport() )
		layout.setSpacing( 0 )
		layout.setMargin( 0 )
		layout.addStretch()
		self.items = []
		self.selected = -1
		self.keyboard = ""
		self.setVerticalScrollBarPolicy( Qt.ScrollBarAlwaysOn )
		self.connect( self.verticalScrollBar(), SIGNAL('valueChanged(int)'), self.scrollBarChanged )
		self.setEditTriggers( QAbstractItemView.NoEditTriggers )

	def scrollBarChanged(self, value):
		self.viewport().move( 0, - value )

	## Map the label or widget of each item with 
	# the corresponding column of the model
	#
	# Example of a valid map:
	# \code
	#  map = [ ('uiModel', 3), ('uiName', 4), ('uiHeadline', 5), ('uiRanking', 6) ]
	#  uiItems.setModelItemMap( map )
	# \endcode
	def setModelItemMap(self, map):
		self.map = map

	## Sets the .ui file that will be used to represent each item
	#  int the list
	#
	# The .ui file should contain QLabels which will be mapped using
	# setModelItemMap().
	def setItemUi(self, uiFile ):
		self.uiFile = uiFile

	## You may inherit this class and reimplement this function if your items,
	# aren't created from ui files or the file is not composed
	# only of simple labels.
	def createItemWidget(self, parent):
		return SearchViewItem( self.uiFile, parent )

	## Reimplement this function if you don't use the map to automatically
	# fill the item widget. Note that the index of the model is inside 
	# 'item.index'.
	def fillItemWidget( self, item ):
		pass

	# Functions required by QAbstractItemView
	def indexAt( self, point ):
		idx = QModelIndex()
		y = 0
		for x in self.items:
			if x.geometry().contains(point):
				return x.index
			y += 1
		return idx

	def keyboardSearch( self, search ):
		search = self.keyboard + str(search).lower()
		found = False
		start = max(self.selected, 0)
		for x in range(start, len(self.items)):
			if str(self.items[x].uiName.text()).lower().startswith( search ):
				found = True
				break
		if found:
			self.selected = x
			self.keyboard = search
			self.highlightSelected()

	def scrollTo( self, index, hint ): 
		pos = None
		if hint == QAbstractItemView.EnsureVisible:
			rect = self.visualRect(index)
			if rect.y() + rect.height() > abs(self.viewport().y()) + self.height():
				# Position at bottom	
				rect = self.visualRect(index)
				pos = rect.y() + rect.height() - self.height() 
				pos = max( pos, 0 )
			elif rect.y() < abs(self.viewport().y()):
				# Position at top
				pos = self.visualRect(index).y()
		elif hint == QAbstractItemView.PositionAtTop:
			pos = self.visualRect(index).y()
		elif hint == QAbstractItemView.PositionAtBottom:
			rect = self.visualRect(index)
			pos = rect.y() + rect.height() - self.height() 
			pos = max( pos, 0 )
		elif hint == QAbstractItemView.PositionAtCenter:
			rect = self.visualRect(index)
			pos = rect.y() + (rect.height()/2) - ( self.height()/2 )
			pos = max( pos, 0 )

		if pos != None:
			self.viewport().move( 0, - pos )

	def visualRect( self, index ):
		for x in self.items:
			if x.index == index:
				return x.geometry()
		return QRect()

	def isIndexHidden( self, index ):
		for x in self.items:
			if x.index == index:
				if x.geometry().y() > self.viewport().y() + self.viewport().height() or \
					x.geometry().y + x.geometry().height() < self.viewport().y():
					return True
				else:
					return False
		return False

	def horizontalOffset(self):
		return 0

	def verticalOffset(self):
		return self.viewport().y()

	def moveCursor( self, action, modifiers ):
		if len(self.items) == 0:
			return QModelIndex()
		if action == QAbstractItemView.MoveUp:
			selected = self.selected - 1
		elif action == QAbstractItemView.MoveDown:
			selected = self.selected + 1
		elif action == QAbstractItemView.MoveHome:
			selected = 0
		elif action == QAbstractItemView.MoveEnd:
			selected = len(self.items) - 1
		elif action == QAbstractItemView.MovePageUp:
			selected = self.selected - 3
		elif action == QAbstractItemView.MovePageDown:
			selected = self.selected + 3
		elif action == QAbstractItemView.MoveNext:
			selected = self.selected + 1
		elif action == QAbstractItemView.MovePrevious:
			selected = self.selected - 1
		elif action == QAbstractItemView.MoveRight:
			selected = self.selected + 1
		elif action == QAbstractItemView.MoveLeft:
			selected = self.selected - 1

		selected = min(selected, len(self.items)-1)
		selected = max(selected, 0)
		if selected != self.selected:
			self.selected = selected
			self.highlightSelected()
		return self.items[self.selected].index

	def setSelection( self, rect, flags ):
		self.selected = -1
		for x in range(len(self.items)):
			if self.items[x].geometry().intersects( rect ):
				self.selected = x
		if self.selected != -1:
			self.selectionModel().select( self.items[self.selected].index, QItemSelectionModel.Current )
		else:
			self.selectionModel().select( QModelIndex(), QItemSelectionModel.Current )
		self.highlightSelected()

	def visualRegionForSelection( self, selection ):
		region = QRegion()
		for x in self.items:
			for y in selection.indexes():
				if x.index == y:
					region.unite( QRegion( x.geometry() ) )
		return region

	def rowsInserted( self, index, start, end ):
		for y in range(start, end+1):
			item = self.createItemWidget( self.viewport() )
			item.index = self.model().index( y, 0, index )
			# Fill in the item
			if self.map:
				# If there is a map, it means that autofilling is enabled
				for x in self.map:
					idx = self.model().index( y, x[1], index )
					exec("item.%s.setText( self.model().data( idx ).toString() )" % x[0] )
			else:
				# Otherwise let the user fill in the item
				self.fillItemWidget( item )
			self.viewport().layout().insertWidget( self.viewport().layout().count() -1, item )
			self.items.append(item)
			self.updateViewport( item.height() )

		if self.selected == -1:
			self.selected = 0
			self.highlightSelected() 

	def updateViewport(self, itemHeight):
		height = 0
		for x in self.items:
			height += x.geometry().height()
		self.viewport().setFixedHeight( height )
		diff = self.viewport().height() - self.height()
		if diff < 0:
			diff = 0
		self.verticalScrollBar().setRange( 0, diff )
		self.verticalScrollBar().setValue( 0 )

	def rowsAboutToBeRemoved( self, index, start, end ):
		s = self.model().index( start, 0, index )
		e = self.model().index( end, 0, index )
		remove = []
		for x in self.items:
			if ( s < x.index or s == x.index ) and (x.index < e or x.index == e):
				remove.append( x )
				x.deleteLater()
		for x in remove:
			del self.items[self.items.index(x)]
		if self.selected >= len(self.items):
			self.selected = -1

	def highlightSelected(self):
		if self.selected < 0:
			return
		for x in range(len(self.items)):
			if x == self.selected:
				self.items[x].setStyleSheet( 'QWidget{background: yellow}' )	
			else:
				self.items[x].setStyleSheet( '' )

## @brief The FullTextSearchDialog class shows a dialog for searching text at all indexed models.
#
# The dialog has a text box for the user input and a combo box to search at one specific
# model or all models that have at least one field indexed.
class FullTextSearchDialog( QDialog ):
	def __init__(self, parent = None):
		QDialog.__init__( self, parent )
		self.setModal( True )
		loadUi( common.uiPath('full_text_search.ui') , self )

		self.result=None

		self.model = FullTextSearchModel(self)
		#self.uiItems = SearchView( self )
		map = [ ('uiModel', 3), ('uiName', 4), ('uiHeadline', 5),
			('uiRanking', 6) ]
		self.uiItems.setModelItemMap( map )
		self.uiItems.setItemUi( common.uiPath('searchviewitem.ui') )
		self.uiItems.setModel( self.model )
		self.layout().insertWidget( 1, self.uiItems )

		self.uiErrorMessage.hide()
		try:
			answer = rpc.session.call('/fulltextsearch', 'indexedModels', rpc.session.context )
			self.uiModel.addItem( _('(Everywhere)'), QVariant( False ) )	
			for x in answer:
				self.uiModel.addItem( x['name'], QVariant( x['id'] ) )
			if len(answer) == 0:
				self.disableQueries( _('<b>Full text search is not configured.</b><br/>Go to <i>Administration - Configuration - Full Text Search - Indexes</i>. Then add the fields you want to be indexed and finally use <i>Update Full Text Search</i>.') )
		except:
			self.disableQueries( _('<b>Full text search module not installed.</b><br/>Go to <i>Administration - Modules administration - Uninstalled Modules</i> and add the <i>full_text_search</i> module.') )

		self.title = _('Tiny ERP Full Text Search')
		self.title_results = _('Tiny ERP Full Text Search (%%d result(s))')

		self.setWindowTitle( self.title )

		self.limit = 4
		self.offset = 0
		self.pushNext.setEnabled( False )
		self.pushPrevious.setEnabled( False )

		self.connect( self.pushAccept, SIGNAL( "clicked( )"), self.open )
		self.connect( self.uiItems, SIGNAL( "doubleClicked(QModelIndex)"), self.open )
		self.connect( self.pushCancel , SIGNAL( "clicked()"), self.reject )
		self.connect( self.pushFind, SIGNAL( "clicked()"), self.find )
		self.connect( self.pushPrevious, SIGNAL( "clicked()" ), self.previous )
		self.connect( self.pushNext, SIGNAL( "clicked()" ), self.next )
		self.show()

	def disableQueries(self, text):
		self.uiModel.setEnabled( False )
		self.pushFind.setEnabled( False )
		self.pushAccept.setEnabled( False )
		self.uiText.setEnabled( False )
		self.uiItems.hide()
		self.uiErrorMessage.setText( text )
		self.uiErrorMessage.show()

	def textToQuery(self):
		q = unicode( self.uiText.text() ).strip()
		while q != q.replace( '  ', ' ' ):
			q = q.replace( '  ', ' ' )
		q = q.replace(' ', '|')
		return q

	def query(self):
		if self.uiModel.currentIndex() == 0:
			model = False
		else:
			model = unicode( self.uiModel.itemData( self.uiModel.currentIndex() ).toString() )
		answer = rpc.session.execute('/fulltextsearch', 'search', self.textToQuery(), self.limit, self.offset , model, rpc.session.context)
		self.model.setList( answer )
		if len(answer) < self.limit:
			self.pushNext.setEnabled( False )
		else:
			self.pushNext.setEnabled( True )
		if self.offset == 0:
			self.pushPrevious.setEnabled( False )
		else:
			self.pushPrevious.setEnabled( True )
		
	def previous(self):
		self.offset = max(0, self.offset - self.limit )
		self.query()
		
	def next(self):
		self.offset = self.offset + self.limit
		self.query()

	def find(self):
		self.offset = 0
		self.query()

	def reload(self):
		self.view.widget.model().removeAll()
		model = self.view.widget.model()
		index1 =  model.index( 1,1 )
		selectionModel = QItemSelectionModel( model )
		selectionModel.select( index1 , QItemSelectionModel.Rows )

	def open( self ):
		idx = self.uiItems.selectionModel().currentIndex()
		if idx.isValid():
			id = self.model.item( idx.row(), 0 ).text()
			model = self.model.item( idx.row(), 2 ).text()
			self.result = ( int(str(id)), unicode(model) )
			self.accept()

class FullTextSearchModel( QStandardItemModel ):
	def __init__(self, parent = None):
		QStandardItemModel.__init__(self, parent)
		self.rootItem = self.invisibleRootItem()
		self.setColumnCount( 7 )
		self.setHeaderData( 0, Qt.Horizontal, QVariant( _("ID") ) )
		self.setHeaderData( 1, Qt.Horizontal, QVariant( _("Model ID") ) )
		self.setHeaderData( 2, Qt.Horizontal, QVariant( _("Model Name") ) )
		# Model Description
		self.setHeaderData( 3, Qt.Horizontal, QVariant( _("Type") ) )
		self.setHeaderData( 4, Qt.Horizontal, QVariant( _("Name") ) )
		self.setHeaderData( 5, Qt.Horizontal, QVariant( _("Text") ) )
		self.setHeaderData( 6, Qt.Horizontal, QVariant( _("Ranking") ) )

		self.serverOrder = ['id', 'model_id', 'model_name', 'model_label', 'name', 'headline', 'ranking']

	def setList(self, list):
		if self.rowCount() > 0:
			self.removeRows(0, self.rowCount())
		for x in list:
			l = [QStandardItem(unicode(x[y])) for y in self.serverOrder ]
			self.rootItem.appendRow( l )
		
# vim:noexpandtab:
