##############################################################################
#
# Copyright (c) 2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id: screen.py 4698 2006-11-27 12:30:44Z ced $
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

from rpc import RPCProxy
import rpc

from widget.model.group import ModelRecordGroup
from widget.model.record import ModelRecord

from common import common

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import widget_search
from toolbar import ToolBar
from action import *


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

		# GUI Stuff
		self.setFrameShape( QFrame.NoFrame )
		self.setWidgetResizable( True )
		self.container = QWidget( self )
		self.setWidget( self.container )

		self.container.show()

		self.searchForm = widget_search.SearchFormWidget(self.container)
		self.connect( self.searchForm, SIGNAL('search()'), self.search )
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

		#self._domain = []
		self.views_preload = {}
		self.rpc = None
		self.views = []
		self.fields = {}
		self._viewIds = []
		self._viewTypes = ['form','tree']
		self.models = None
		self.__current_model = None

		self.__current_view = 0

		self._addAfterNew = False

	def setPreloadedViews(self, views):
		self.views_preload = views

	def preloadedViews(self, views):
		return self.views_preload
		
	def setViewIds(self, ids):
		self._viewIds = ids[1:]
		view = self.addViewById( ids[0] )
		self.setView( view )
		self.display()

	def viewIds(self):
		return self._viewIds

	def setViewTypes(self, types):
		if not types:
			self._viewTypes = []
			return
		self._viewTypes = types[1:]
		view = self.addViewByType( types[0] )
		self.setView(view)
		self.display()

	def viewTypes(self):
		return self._viewTypes

	def setAddAfterNew(self, value):
		self._addAfterNew = value

	def addAfterNew(self):
		return self._addAfterNew

	#def setDomain(self, value):
		#self._domain = value

	#def domain(self):
		#return self._domain

	## @brief Sets whether the screen is embedded.
	#
	# Embedded screens don't show the search or toolbar widgets.
	# By default embedded is True so it doesn't load unnecessary forms.
	def setEmbedded(self, value):
		self._embedded = value
		if value:
			self.searchForm.hide()
			self.toolBar.hide()
		else:
			self.searchForm.show()
			self.toolBar.show() 
			if self.current_view and self.current_view.view_type == 'tree':
				self.loadSearchForm()

	def embedded(self):
		return self._embedded

	def loadSearchForm(self):
		if self.current_view.view_type == 'tree' and not self._embedded: 
			form = rpc.session.execute('/object', 'execute', self.resource, 'fields_view_get', False, 'form', self.context)
			self.searchForm.setup( form['arch'], form['fields'], self.resource )
			self.searchForm.show()
		else:
			self.searchForm.hide()

	def triggerAction(self):
		if not self.id_get():
			return
		# We expect a TinyAction here
		action = self.sender()

		id = self.id_get()
		ids = self.selectedIds()

		if action.type() != 'relate':
			self.save_current()
			self.display()

		action.execute( id, ids )

		if action.type() != 'relate':
			self.reload()

	# Sets the current widget of the Screen
	def setView(self, widget):
		if self.containerView:
			self.disconnect(self.containerView, SIGNAL("activated()"), self.switchView)
			self.disconnect(self.containerView, SIGNAL("currentChanged(PyQt_PyObject)"), self.currentChanged)
			self.containerView.hide()

		self.containerView = widget
		widget.show()
		self.connect(widget, SIGNAL("activated()"), self.switchView)
		self.connect(widget, SIGNAL("currentChanged(PyQt_PyObject)"), self.currentChanged)
		
		self.loadSearchForm()

		self.layout.insertWidget( 0, widget )
		self.ensureWidgetVisible( widget )

	# Searches with the current parameters of the search form and loads the
	# models that fit the criteria.
	def search( self ):
		value = self.searchForm.getValue()
		self.models.setFilter( value )
		self.models.update()

	# Slot to recieve the signal from a view when the current item changes
	def currentChanged(self, model):
		self.current_model = model

	## @brief Sets the RecordModelGroup this Screen should show.
	# @param models ModelRecordGroup object.
	def setModelGroup(self, modelGroup):
		self.name = modelGroup.resource
		self.resource = modelGroup.resource
		self.context = modelGroup.context
		self.rpc = RPCProxy(self.resource)

		self.models = modelGroup
		if len(modelGroup.models):
			self.current_model = modelGroup.models[0]
		else:
			self.current_model = None

		modelGroup.addFields(self.fields)
		self.fields.update(modelGroup.fields)

	def _get_current_model(self):
		return self.__current_model

	#
	# Check more or less fields than in the screen !
	#
	def _set_current_model(self, value):
		self.__current_model = value
		try:
			pos = self.models.models.index(value)
		except:
			pos = -1
		if value and value.id:
			id = value.id
		else:
			id = -1
		self.emit(SIGNAL('recordMessage(int,int,int)'), pos, len(self.models.models or []), id)
		if self.__current_model:
			if self.current_view:
				self.current_view.setSelected(self.__current_model.id)
		return True
	current_model = property(_get_current_model, _set_current_model)

	def switchView(self):
		if self.current_view: 
			self.current_view.store()

		if self.current_model and ( self.current_model not in self.models.models ):
			self.current_model = None

		#if len(self._viewTypes) or len(self._viewIds):
		#self.loadNextView()
		if self.loadNextView():
			self.__current_view = len(self.views) - 1
		else:
			self.__current_view = (self.__current_view + 1) % len(self.views)

		self.setView(self.current_view)
	    	if self.current_model:
			self.current_model.setValidate()
		self.display()

	## @brief Loads the next view pending to be loaded.
	# If there is no view pending it returns False, otherwise returns True.
	def loadNextView(self):
		if self._viewIds:
			self.addViewById( self._viewIds.pop(0) )
			return True
		elif self._viewTypes:
			self.addViewByType( self._viewTypes.pop(0) )
			return True
		else:
			return False

	#def add_view_custom(self, arch, fields, display=False, toolbar={}):
	def addCustomView(self, arch, fields, display=False, toolbar={}):
		return self.addView(arch, fields, display, True, toolbar=toolbar)

	## @brief Adds a view given its id.
	# @param id View id to load or False if you want to load given view_type.
	# @param display Whether you want the added view to be shown (True) or only loaded (False).
	# @return The view widget
	def addViewById(self, id, display=False):
		# TODO: By now we set toolbar to True always. Even when Screen is embedded
		view = self.rpc.fields_view_get(id, False, self.context, True)
		if 'type' in view:
			if view['type'] in self._viewTypes:
				self._viewTypes.remove( view['type'] )
		return self.addView(view['arch'], view['fields'], display, toolbar=view.get('toolbar', False))
		
	## @brief Adds a view given a view type.
	# @param type View type ('form', 'tree', 'calendar', 'graph'...). 
	# @param display Whether you want the added view to be shown (True) or only loaded (False).
	# @return The view widget
	def addViewByType(self, type, display=False):
		if type in self.views_preload:
			return self.addView(self.views_preload[type]['arch'], self.views_preload[type]['fields'], display, toolbar=self.views_preload[type].get('toolbar', False))
		else:
			# TODO: By now we set toolbar to True always. Even when the Screen is embedded
			view = self.rpc.fields_view_get(False, type, self.context, True)
			return self.addView(view['arch'], view['fields'], display, toolbar=view.get('toolbar', False))
		
	## @brief Adds a view given it's XML description and fields
	# @param arch XML string: typically 'arch' field returned by model fields_view_get() function.
	# @param fields Fields dictionary containing each field (widget) properties.
	# @param display Whether you want the added view to be shown (True) or only loaded (False)
	# @param custom If True, fields are added to those existing in the model
	# @return The view widget
	def addView(self, arch, fields, display=False, custom=False, toolbar={}):
		def _parse_fields(node, fields):
			if node.nodeType == node.ELEMENT_NODE:
				if node.localName=='field':
					attrs = common.node_attributes(node)
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

		models = self.models.models
		if self.current_model and (self.current_model not in models):
			models = models + [self.current_model]
		if custom:
			self.models.addCustomFields(fields)
		else:
			self.models.addFields(fields)

		self.fields = self.models.fields

		dom = xml.dom.minidom.parseString(arch.encode('utf-8'))
		from widget.view.viewfactory import ViewFactory
		view, on_write = ViewFactory.create(self, self.resource, dom, self.fields)
		self.setOnWrite( on_write )

		self.views.append(view)
		self.loadActions( toolbar )

		if display:
			self.__current_view = len(self.views) - 1
			self.current_view.display(self.current_model, self.models)
			self.setView(view)
		return view

	def loadActions( self, actions ):
		self.actions = ActionFactory.create( self, actions, self.resource )
		if self.actions:
			for action in self.actions:
				self.connect( action, SIGNAL('triggered()'), self.triggerAction )
			self.toolBar.setup( self.actions )

	def isReadOnly(self):
		return self.current_view.isReadOnly()

	def new(self, default=True):
		if self.current_view and self.current_view.view_type == 'tree' \
				and self.current_view.isReadOnly():
			self.switchView()
		model = self.models.newModel(default, self.models.domain(), self.context)

		if (not self.current_view) or self.current_view.model_add_new or self._addAfterNew:
			self.models.addModel(model, self.new_model_position())

		if self.current_view:
			self.current_view.reset()

		self.current_model = model
		self.display()
		return self.current_model

	def new_model_position(self):
		position = -1
		if self.current_view and self.current_view.view_type =='tree' \
			    and self.current_view.isReadOnly():
			#and self.current_view.editable == 'top':
			position = 0
		return position

	def setOnWrite(self, func_name):
		self.models.on_write = func_name

	def cancel_current(self):
		self.current_model.cancel()

	def save_current(self):
 		if not self.current_model:
 			return False
 		self.current_view.store()
		
		id = False
		if self.current_model.validate():
			id = self.current_model.save(reload=True)
		else:
			self.current_view.display(self.current_model, self.models)
			return False
		
		if self.current_view.view_type == 'tree':
			for model in self.models.models:
				if model.isModified():
					if model.validate():
						id = model.save(reload=True)
					else:
						self.current_model = model
						self.display()
						return False
			self.display()

		if self.current_model not in self.models:
			self.models.addModel(self.current_model)
		self.display()
		return id

	def _getCurrentView(self):
		if not len(self.views):
			return None
		return self.views[self.__current_view]
	current_view = property(_getCurrentView)

	def get(self):
		if not self.current_model:
			return None
		self.current_view.store()
		return self.current_model.get()

	def isModified(self):
		if not self.current_model:
			return False
		self.current_view.store()
		res = False
		if self.current_view.view_type != 'tree':
			res = self.current_model.isModified()
		else:
			for model in self.models.models:
				if model.isModified():
					res = True
		return res 

	#
	# To write
	#
	def reload(self):		
		self.current_model.reload()
		self.display()

	def remove(self, unlink = False):
		ids = self.selectedIds()
		for x in ids:
			model = self.models[x]
			idx = self.models.models.index(model)
			self.models.remove( model )
			if self.models.models:
				idx = min(idx, len(self.models.models)-1)
				self.current_model = self.models.models[idx]
			else:
				self.current_model = None
		if unlink and id:
			self.rpc.unlink(ids)	
		self.display()
		if ids:
			return True
		else:
			return False

	def load(self, ids):
		self.current_view.reset()
		self.models.load( ids, display =True )
		if ids:
			self.display(ids[0])
		else:
			self.current_model = None
			self.display()

	def display(self, res_id=None):
		if res_id:
			self.current_model = self.models[res_id]
		if self.views:
			self.current_view.display(self.current_model, self.models)

	def display_next(self):
		self.current_view.store()
		if self.current_model in self.models.models:
			idx = self.models.models.index(self.current_model)
			idx = (idx+1) % len(self.models.models)
			self.current_model = self.models.models[idx]
		else:
			self.current_model = len(self.models.models) and self.models.models[0]
		if self.current_model:
			self.current_model.setValidate()
		self.display()

	def display_prev(self):
		self.current_view.store()
		if self.current_model in self.models.models:
			idx = self.models.models.index(self.current_model)-1
			if idx<0:
				idx = len(self.models.models)-1
			self.current_model = self.models.models[idx]
		else:
			self.current_model = len(self.models.models) and self.models.models[-1]

		if self.current_model:
			self.current_model.setValidate()
		self.display()

	def selectedIds(self):
		return self.current_view.selectedIds()

	def id_get(self):
		if self.current_model:
			return self.current_model.id
		else:
			return None

	def ids_get(self):
		return [x.id for x in self.models if x.id]

	def clear(self):
		self.models.clear()
		self.display()

	def on_change(self, callback):
		self.current_model.on_change(callback)
		self.display()

# vim:noexpandtab:
