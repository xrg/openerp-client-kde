##############################################################################
#
# Copyright (c) 2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
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

import xml.dom.minidom

from Koo.Rpc import RpcProxy
from Koo import Rpc

from Koo.Model.Group import RecordGroup
from Koo.Model.Record import Record
from Koo.View.ViewFactory import ViewFactory

from Koo.Common import Common
from Koo.Common import Options
from Koo.Common.ViewSettings import *

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from Koo.Search import SearchFormWidget
from Koo.Plugins import *
from ToolBar import ToolBar
from Action import *
from ViewQueue import *


## @brief The Screen class is a widget that provides an easy way of handling multiple views.
#
# This class is capable of managing various views of the same model and provides
# functions for moving to the next and previous record.
#
# If neither setViewTypes() nor setViewIds() are called, form and tree views (in this order)
# will be used. If you use only a single 'id' and say it's a 'tree', one you try to switchView
# the default 'form' view will be shown. If you only want to show the 'tree' view, use 
# setViewTypes( [] ) or setViewTypes( ['tree'] )
# When you add a new view by it's ID the type of the given view is removed from the list of
# view types. (See: addViewById() )
#
class Screen(QScrollArea):

	def __init__(self, parent=None):
		QScrollArea.__init__(self, parent)
		self.setFocusPolicy( Qt.NoFocus )

		# GUI Stuff
		self.setFrameShape( QFrame.NoFrame )
		self.setWidgetResizable( True )
		self.container = QWidget( self )
		self.setWidget( self.container )

		self.container.show()

		self.searchForm = SearchFormWidget(self.container)
		self.connect( self.searchForm, SIGNAL('search()'), self.search )
		self.connect( self.searchForm, SIGNAL('keyDownPressed()'), self.setFocusToView )
		self.searchForm.hide()
		self.containerView = None

		self.toolBar = ToolBar(self)
		self.toolBar.hide()

		self.layout = QHBoxLayout()
		self.layout.setSpacing( 0 )
		self.layout.setContentsMargins( 0, 0, 0, 0 )
		self.layout.addWidget( self.toolBar )

		vLay = QVBoxLayout( self.container )
		vLay.setContentsMargins( 0, 0, 0, 0 )
		vLay.addWidget( self.searchForm )
		vLay.addLayout( self.layout )

		# Non GUI Stuff
		self.actions = []

		self._embedded = True

		self.views_preload = {}
		self.rpc = None
		self.name = None
		self.views = {}
		self.fields = {}
		self.group = None
		self._currentRecordPosition = None
		self._currentRecord = None
		self._currentView = -1
		self._previousView = -1

		self._viewQueue = ViewQueue()

	def setFocusToView(self):
		self.currentView().setFocus()

	def sizeHint(self):
		return self.container.sizeHint()

	def setPreloadedViews(self, views):
		self.views_preload = views

	def preloadedViews(self, views):
		return self.views_preload
		
	def setupViews(self, types, ids):
		self._viewQueue.setup( types, ids )
		# Try to load only if model group has been set
		if self.name:
			self.switchView()

	def setViewIds(self, ids):
		self._viewQueue.setViewIds( ids )
		# Try to load only if model group has been set
		if self.name:
			self.switchView()

	def viewIds(self):
		return self._viewIds

	def setViewTypes(self, types):
		self._viewQueue.setViewTypes( types )
		# Try to load only if model group has been set
		if self.name:
			self.switchView()

	## @brief Sets whether the screen is embedded.
	#
	# Embedded screens don't show the search or toolbar widgets.
	# By default embedded is True so it doesn't load unnecessary forms.
	def setEmbedded(self, value):
		self._embedded = value
		self.setToolbarVisible( not value )
		self.setSearchFormVisible( not value )

	## @brief Returns True if the Screen acts in embedded mode.
	def embedded(self):
		return self._embedded

	def setToolbarVisible(self, value):
		self._toolbarVisible = value
		self.toolBar.setVisible( value )

	def setSearchFormVisible(self, value):
		self._searchFormVisible = value
		self.searchForm.setVisible( value )
		if value:
			if self.currentView() and self.currentView().showsMultipleRecords():
				self.loadSearchForm()

	def loadSearchForm(self):
		if self.currentView().showsMultipleRecords() and not self._embedded: 
			if not self.searchForm.isLoaded():
				form = Rpc.session.execute('/object', 'execute', self.resource, 'fields_view_get', False, 'form', self.context)
				self.searchForm.setup( form['arch'], form['fields'], self.resource )

			if self.searchForm.isEmpty():
				self.searchForm.hide()
			else:
				self.searchForm.show()
		else:
			self.searchForm.hide()

	def triggerAction(self):
		# We expect a Screen.Action here
		action = self.sender()

		# Do not trigger action if there is no record selected. This is
		# only permitted for plugins.
		if not self.currentId() and action.type() != 'plugin':
			return

		id = self.currentId()
		ids = self.selectedIds()

		if action.type() != 'relate':
			self.save()
			self.display()

		action.execute( id, ids )

		if action.type() != 'relate':
			self.reload()

	## @brief Sets the current widget of the Screen
	def setView(self, widget):
		if self.containerView:
			self.disconnect(self.containerView, SIGNAL("activated()"), self.activate )
			self.disconnect(self.containerView, SIGNAL("currentChanged(PyQt_PyObject)"), self.currentChanged)
			self.containerView.hide()

		self.containerView = widget
		# Calling first "loadSearchForm()" because when the search form is hidden
		# it looks better to the user. If we show the widget and then hide the search
		# form it produces an ugly flickering.
		self.loadSearchForm()
		widget.show()
		self.connect(widget, SIGNAL("activated()"), self.activate )
		self.connect(widget, SIGNAL("currentChanged(PyQt_PyObject)"), self.currentChanged)

		# Set focus proxy so other widgets can try to setFocus to us
		# and the focus is set to the expected widget.
		self.setFocusProxy( self.containerView )

		self.layout.insertWidget( 0, widget )
		self.ensureWidgetVisible( widget )

	def activate( self ):
		self.emit( SIGNAL('activated()') )

	def close( self ):
		self.emit( SIGNAL('closed()') )

	## @brief Searches with the current parameters of the search form and loads the
	# models that fit the criteria.
	def search( self ):
		value = self.searchForm.value()
		self.group.setFilter( value )
		self.group.update()
		if self.group.count() > 0:
			self.setCurrentRecord( self.group.recordByIndex( 0 ) )
		else:
			self.setCurrentRecord( None )
		self.display()

	# Slot to recieve the signal from a view when the current item changes
	def currentChanged(self, model):
		self.setCurrentRecord( model )
		self.emit( SIGNAL('currentChanged()') )

	## @brief Sets the RecordGroup this Screen should show.
	# @param group RecordGroup object.
	def setRecordGroup(self, group):
		if not group:
			self.group = None
			self._currentRecord = None
			self._currentRecordPosition = None
			# Call setCurrentRecord() after setting self.group
			# because it will emit a signal with the count of elements
			# which must be 0.
			self.setCurrentRecord( None )
			return

		self.name = group.resource
		self.resource = group.resource
		self.context = group.context()
		self.rpc = RpcProxy(self.resource)

		self.group = group
		self._currentRecord = None
		self._currentRecordPosition = None

		group.addFields(self.fields)
		self.fields.update(group.fields)

	## @brief Returns a reference the current record (Record).
	def currentRecord(self):
		# Checking _currentRecordPosition before count() can save a search() call to the server because
		# count() will execute a search() in the server if no items have been loaded yet. What happens is
		# that the first time a screen with a TreeView is shown currentRecord() will be called but there
		# will be no currentRecord. TreeView then will set the appropiate order by loading settings from 
		# the server through restoreViewSettings, and KooModel will load data on demand.
		if self._currentRecordPosition >= 0 and self.group.count():
			# Use modelByIndex because this ensures all missing fields of the model
			# are loaded. For example, the model could have been loaded in tree view
			# but now might need more fields for form view.
			return self.group.modelByIndex( self._currentRecordPosition )
		else:
			# New records won't have that problem (althouth the problem might be that
			# fields haven't been created yet??)
			return self._currentRecord

	## @brief Sets the current record.
	#
	# Note that value will be a reference to the Record.
	def setCurrentRecord(self, value):
		self._currentRecord = value
		if self.group and self.group.recordExists( value ):
			pos = self.group.indexOfRecord( value )
		else:
			pos = -1
		self._currentRecordPosition = pos
		if value and value.id:
			id = value.id
		else:
			id = -1
		if self.group:
			count = self.group.count()
		else:
			count = 0
		self.emit(SIGNAL('recordMessage(int,int,int)'), pos, count, id)
		if self._currentRecord:
			if self.currentView():
				self.currentView().setSelected(self._currentRecord.id)

	## @brief Switches to the next view in the queue of views.
	def switchView(self, viewType = None):
		if self.currentView(): 
			self.currentView().store()

		if self.currentRecord() and ( not self.group.recordExists( self.currentRecord() ) ):
			self.setCurrentRecord( None )

		if viewType:
			self._previousView = self._currentView
			self._currentView = self._viewQueue.indexFromType( viewType )
		else:
			if self._currentView >= 0:
				# Swap currentView and previousView values
				self._currentView, self._previousView = self._previousView, self._currentView
			else:
				self._currentView = 0
			# The second time switchView is executed, currentView might get -1
			# and we want it in fact to be 1 ...
			self._currentView = abs(self._currentView)
			# ... unless there's only one view
			self._currentView = min(self._currentView, self._viewQueue.count()-1)

		self.setView( self.currentView() )
	    	if self.currentRecord():
			self.currentRecord().setValidate()
		self.display()

	## @brief Loads the next view pending to be loaded.
	# If there is no view pending it returns False, otherwise returns True.
	def loadNextView(self):
		if self._viewQueue.isEmpty():
			return False

		(id, type) = self._viewQueue.next()
		self.addViewByIdAndType( id, type )
		return True


	## @brief Adds a view given it's id and type.
	#
	# This function is needed to resemble server's fields_view_get function. This 
	# function wasn't necessary but accounting module needs it because it tries to
	# open a view with it's ID but reimplements fields_view_get and checks the view
	# type.
	#
	# @see AddViewById
	# @see AddViewByType
	def addViewByIdAndType(self, id, type, display=False):
		if type in self.views_preload:
			return self.addView(self.views_preload[type]['arch'], self.views_preload[type]['fields'], display, toolbar=self.views_preload[type].get('toolbar', False), id=self.views_preload[type].get('view_id',False))
		else:
			# By now we set toolbar to True always. Even when the Screen is embedded.
			# This way we don't force setting the embedded option in the class constructor
			# and can be set later.
			view = self.rpc.fields_view_get(id, type, self.context, True)
			return self.addView(view['arch'], view['fields'], display, toolbar=view.get('toolbar', False), id=view['view_id'])
		
	## @brief Adds a view given its id.
	# @param id View id to load or False if you want to load given view_type.
	# @param display Whether you want the added view to be shown (True) or only loaded (False).
	# @return The view widget
	# 
	# @see AddViewByType
	# @see AddViewByIdAndType
	def addViewById(self, id, display=False):
		# By now we set toolbar to True always. Even when the Screen is embedded.
		# This way we don't force setting the embedded option in the class constructor
		# and can be set later.
		view = self.rpc.fields_view_get(id, False, self.context, True)
		return self.addView(view['arch'], view['fields'], display, toolbar=view.get('toolbar', False), id=id)
		
	## @brief Adds a view given a view type.
	# @param type View type ('form', 'tree', 'calendar', 'graph'...). 
	# @param display Whether you want the added view to be shown (True) or only loaded (False).
	# @return The view widget
	#
	# @see AddViewById
	# @see AddViewByIdAndType
	def addViewByType(self, type, display=False):
		if type in self.views_preload:
			return self.addView(self.views_preload[type]['arch'], self.views_preload[type]['fields'], display, toolbar=self.views_preload[type].get('toolbar', False), id=self.views_preload[type].get('view_id',False))
		else:
			# By now we set toolbar to True always. Even when the Screen is embedded.
			# This way we don't force setting the embedded option in the class constructor
			# and can be set later.
			view = self.rpc.fields_view_get(False, type, self.context, True)
			return self.addView(view['arch'], view['fields'], display, toolbar=view.get('toolbar', False), id=view['view_id'])
		
	## @brief Adds a view given it's XML description and fields
	# @param arch XML string: typically 'arch' field returned by model fields_view_get() function.
	# @param fields Fields dictionary containing each field (widget) properties.
	# @param display Whether you want the added view to be shown (True) or only loaded (False)
	# @param toolbar Toolbar information as returned from fields_view_get server function.
	# @param id View id. This parameter is used for storing and loading settings for the view. If id=False, no
	#		settings will be stored/loaded.
	# @return The view widget
	def addView(self, arch, fields, display=False, toolbar={}, id=False):
		def _parse_fields(node, fields):
			if node.nodeType == node.ELEMENT_NODE:
				if node.localName=='field':
					attrs = Common.nodeAttributes(node)
					if attrs.get('widget', False):
						if attrs['widget']=='one2many_list':
							attrs['widget']='one2many'
						attrs['type'] = attrs['widget']
					try:
						fields[attrs['name']].update(attrs)
					except:
						print "-"*30,"\n malformed tag for :", attrs
						print "-"*30
						raise						
			for node2 in node.childNodes:
				_parse_fields(node2, fields)
		dom = xml.dom.minidom.parseString(arch.encode('utf-8'))
		_parse_fields(dom, fields)

		self.group.addFields(fields)

		self.fields = self.group.fields

		dom = xml.dom.minidom.parseString(arch.encode('utf-8'))
		view = ViewFactory.create(id, self, self.resource, dom, self.fields)
		self.setOnWriteFunction( view.onWriteFunction() )
		# Load view settings
		view.setViewSettings( ViewSettings.load( view.id ) )

		self.views[ view.viewType() ] = view
		self.loadActions( toolbar )

		if display:
			if not self._viewQueue.typeExists( view.viewType() ):
				self._viewQueue.addViewType( view.viewType() )
			self._currentView = self._viewQueue.indexFromType( view.viewType() )
			self.currentView().display(self.currentRecord(), self.group)
			self.setView(view)
		return view

	## @brief Loads all actions associated with the current model including plugins.
	def loadActions( self, actions ):
		self.actions = ActionFactory.create( self, actions, self.resource )
		if self.actions:
			for action in self.actions:
				self.connect( action, SIGNAL('triggered()'), self.triggerAction )
			# If there's only one action it will be the 'Print Screen' action
			# that is added "manually" by ActionFactory. In those cases in which
			# Print Screen is the only action we won't show it in the toolbar. We
			# don't consider Plugins a good reason to show the toolbar either.
			# This way dashboards won't show the toolbar, though the option will
			# remain available in the menu for those screens that don't have any
			# actions configured in the server, but Print Screen can be useful.
			if len(self.actions) > 1 + len(Plugins.list(self.resource)) and Options.options['show_toolbar']:
				self.toolBar.setup( self.actions )

	## @brief Returns True if the current view is read-only. Returns False if it's read-write.
	def isReadOnly(self):
		return self.currentView().isReadOnly()

	def new(self, default=True):
		if self.currentView() and self.currentView().showsMultipleRecords() \
				and self.currentView().isReadOnly():
			self.switchView()

		record = self.group.create( default, self.newRecordPosition(), self.group.domain(), self.context )

		if self.currentView():
			self.currentView().reset()

		self.setCurrentRecord( record )
		self.display()

		if self.currentView():
			self.currentView().startEditing()
		return self.currentRecord()

	def newRecordPosition(self):
		if self.currentView() and self.currentView().addOnTop():
			return 0
		else:
			return -1 

	def setOnWriteFunction(self, functionName):
		self.group.setOnWriteFunction( functionName )

	## @brief Stores all modified models.
	def save(self):
 		if not self.currentRecord():
 			return False
 		self.currentView().store()
		
		id = False
		if self.currentRecord().validate():
			id = self.currentRecord().save(reload=True)
		else:
			self.currentView().display(self.currentRecord(), self.group)
			return False
		
		if self.currentView().showsMultipleRecords():
			for record in self.group.modifiedRecords():
				if record.validate():
					id = record.save(reload=True)
				else:
					self.setCurrentRecord( record )
					self.display()
					return False
			self.display()

		self.display()
		return id

	## @brief Reloads 
	def reload(self):
		if not self.currentView().showsMultipleRecords():
			if self.currentRecord():
				self.currentRecord().reload()
				self.display()
			return

		id = 0
		idx = -1
		if self.currentRecord():
			id = self.currentId()
			idx = self.group.indexOfRecord(self.currentRecord())
			
		self.group.update()
		if id:
			record = self.group.modelById( id )
			
			if record:
				self.setCurrentRecord( record )
			else:
				# If what it was the current record no longer exists
				# at least keep index position
				idx = min( idx, self.group.count() - 1 )
				if idx >= 0:
					self.setCurrentRecord( self.group.recordByIndex( idx ) )
				else:
					self.setCurrentRecord( None )
		else:
			self.setCurrentRecord( None )
		self.display()

	## @brief Removes all new records and marks all modified ones as not loaded.
	def cancel(self):
		idx = -1
		if self.currentRecord():
			idx = self.group.indexOfRecord( self.currentRecord() )
			
		self.group.cancel()
		if idx != -1:
			idx = min( idx, self.group.count() - 1 )
			if idx >= 0:
				self.setCurrentRecord( self.group.recordByIndex( idx ) )
			else:
				self.setCurrentRecord( None )
			self.display()

	## @brief Returns a reference to the current view.
	def currentView(self):
		if self._currentView < 0:
			return None
		type = self._viewQueue.typeFromIndex( self._currentView )
		if not type in self.views:
			(id, type) = self._viewQueue.viewFromType( type )
			self.addViewByIdAndType( id, type )
		return self.views[ type ]

	## @brief Returns a dictionary with all field values for the current record. 
	def get(self):
		if not self.currentRecord():
			return None
		self.currentView().store()
		return self.currentRecord().get()

	## @brief Returns True if any record has been modified. Returns False otherwise.
	def isModified(self):
		if not self.currentRecord():
			return False
		self.currentView().store()
		res = False
		if self.currentView().showsMultipleRecords():
			return self.group.isModified()
		else:
			return self.currentRecord().isModified()

	## @brief Removes all selected ids.
	#
	# If unlink is False (the default) records are only removed from the list. If
	# unlink is True records will be removed from the server too.
	def remove(self, unlink = False):
		ids = self.selectedIds()
		if unlink and ids:
			# Remove records with id None as they would cause an exception
			# trying to remove from the server 
			idsToUnlink = [x for x in ids if x != None]
			# It could be that after removing records with id == None
			# there are no records to remove from the database. That is,
			# all records that should be removed are new and not stored yet.
			if idsToUnlink:
				unlinked = self.rpc.unlink( idsToUnlink )	
				# Try to be consistent with database
				# If records could not be removed from the database
				# don't remove them on the client. Don't report it directly
				# though as probably an exception (Warning) has already
				# been shown to the user.
				if not unlinked:
					return False
		for x in ids:
			model = self.group[x]
			idx = self.group.indexOfRecord( model )
			self.group.remove( model )
			if self.group.count():
				idx = min(idx, self.group.count() - 1)
				self.setCurrentRecord( self.group.recordByIndex( idx ) )
			else:
				self.setCurrentRecord( None )
		self.display()
		if ids:
			return True
		else:
			return False

	def load(self, ids):
		self.currentView().reset()
		self.group.load( ids, display =True )
		if ids:
			self.display(ids[0])
		else:
			self.setCurrentRecord( None )
			self.display()

	## @brief Displays the record with id 'id' or refreshes the current record if 
	# no id is given.
	def display(self, id=None):
		if id:
			self.setCurrentRecord( self.group[id] )
		if self.views:
			self.currentView().display(self.currentRecord(), self.group)

	## @brief Moves current record to the next one in the list and displays it in the 
	# current view.
	def displayNext(self):
		self.currentView().store()
		if self.group.recordExists( self.currentRecord() ):
			idx = self.group.indexOfRecord(self.currentRecord())
			idx = (idx+1) % self.group.count()
			self.setCurrentRecord( self.group.modelByIndex(idx) )
		else:
			self.setCurrentRecord( self.group.count() and self.group.modelByIndex(0) )
		if self.currentRecord():
			self.currentRecord().setValidate()
		self.display()

	## @brief Moves current record to the previous one in the list and displays it in the 
	# current view.
	def displayPrevious(self):
		self.currentView().store()
		if self.group.recordExists( self.currentRecord() ):
			#idx = self.group.records.index(self.currentRecord())-1
			idx = self.group.indexOfRecord(self.currentRecord())-1
			if idx<0:
				idx = self.group.count()-1
			self.setCurrentRecord( self.group.modelByIndex(idx) )
		else:
			self.setCurrentRecord( self.group.count() and self.group.modelByIndex(-1) )

		if self.currentRecord():
			self.currentRecord().setValidate()
		self.display()

	## @brief Returns all selected record ids.
	def selectedIds(self):
		return self.currentView().selectedIds()

	## @brief Returns the current record id.
	def currentId(self):
		if self.currentRecord():
			return self.currentRecord().id
		else:
			return None

	## @brief Returns a list with all loaded (or preloaded) record ids.
	def allIds(self):
		return [x.id for x in self.group if x.id]

	## @brief Clears the list of records and refreshes the view.
	#
	# Note that this won't remove the records from the database. But clears
	# the records from the model. It means that sometimes you might want to
	# use setRecordGroup( None ) instead of calling clear(). This is what
	# OneToMany and ManyToMany widgets do, for example.
	# @see remove()
	def clear(self):
		self.group.clear()
		self.display()

	# Stores settings of all opened views
	def storeViewSettings(self):
		for view in self.views.values():
			ViewSettings.store( view.id, view.viewSettings() )

# vim:noexpandtab:
