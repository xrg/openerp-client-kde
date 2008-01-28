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


## @brief The Screen class is a widget that provides an easy way of handling multiple views.
#
# This class is capable of managing various views of the same model and provides
# functions for moving to the next and previous record.

class Screen(QScrollArea):

	## @brief Constructor
	#
	# @param model_name Name of the model this widget will handle.
	# @param view_ids View ids you want Screen to handle
	# @param view_type 
	# @param parent
	# @param context 
	def __init__(self, model_name, view_ids=[], view_type=['form','tree'], parent=None, context={}, views_preload={}, tree_saves=True, domain=[], create_new=False, hastoolbar=False):

		QScrollArea.__init__(self, parent)

		self.setFrameShape( QFrame.NoFrame )
		self.setWidgetResizable( True )

		self.hastoolbar = hastoolbar
		self.create_new = create_new
		self.name = model_name
		self.domain = domain
		self.views_preload = views_preload
		self.resource = model_name
		self.rpc = RPCProxy(model_name)
		self.context = context
		self.context.update(rpc.session.context)
		self.views = []
		self.fields = {}
		self.view_ids = view_ids
		self.models = None
		self.setModels( ModelRecordGroup(model_name, self.fields, parent=self, context=self.context) )
		self.current_model = None

		self.__current_view = 0

		if view_type:
			self.view_to_load = view_type[1:]
			view_id = False
			if view_ids:
				view_id = view_ids.pop(0)
			view = self.add_view_id(view_id, view_type[0])
			self.setView(view)

		self.display()

	def setView(self, widget):
		if self.widget():
			wid = self.takeWidget()
			# TODO: The widget isn't properly freed. Try for example to
			# remove the 'disconnect' and use double click multiple times
			# to switch from list to form. You'll see the frickerying due
			# to all connected signals!
			self.disconnect(wid, SIGNAL("activated()"), self.switchView)
			self.disconnect(wid, SIGNAL("currentChanged(int)"), self.currentChanged)
			wid.setParent( None )
			del wid

		self.connect(widget, SIGNAL("activated()"), self.switchView)
		self.connect(widget, SIGNAL("currentChanged(int)"), self.currentChanged)
		self.setWidget( widget )
		self.ensureWidgetVisible( widget )

	def currentChanged(self, id):
		self.current_model = None
		for i in self.models.models:
			if i.id == id:
				self.current_model = i

	def setModels(self, models):
		self.models = models
		if len(models.models):
			self.current_model = models.models[0]
		else:
			self.current_model = None

		models.addFields(self.fields)
		self.fields.update(models.fields)

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

		if len(self.view_to_load):
			self.load_view_to_load()
			self.__current_view = len(self.views) - 1
		else:
			self.__current_view = (self.__current_view + 1) % len(self.views)

		self.setView(self.current_view)
	    	if self.current_model:
			self.current_model.setValidate()
		self.display()

	def load_view_to_load(self):
		if len(self.view_to_load):
			if self.view_ids:
				view_id = self.view_ids.pop(0)
				view_type = self.view_to_load.pop(0)
			else:
				view_id = False
				view_type = self.view_to_load.pop(0)
			self.add_view_id(view_id, view_type)

	def add_view_custom(self, arch, fields, display=False, toolbar={}):
		return self.add_view(arch, fields, display, True, toolbar=toolbar)

	## @brief Adds a view given its id or view_type
	# @param view_id View id to load or False if you want to load given view_type
	# @param view_type View type ('form', 'tree', 'calendar', 'graph'...). Only used if view_id = False.
	# @param display Whether you want the added view to be shown (True) or only loaded (False)
	def add_view_id(self, view_id, view_type, display=False):
		if view_type in self.views_preload:
			return self.add_view(self.views_preload[view_type]['arch'], self.views_preload[view_type]['fields'], display, toolbar=self.views_preload[view_type].get('toolbar', False))
		else:
			view = self.rpc.fields_view_get(view_id, view_type, self.context, self.hastoolbar)
			return self.add_view(view['arch'], view['fields'], display, toolbar=view.get('toolbar', False))
	
	## @brief Adds a view given it's XML description and fields
	# @param arch XML string: typically 'arch' field returned by model fields_view_get() function.
	# @param fields Fields dictionary containing each field (widget) properties.
	# @param display Whether you want the added view to be shown (True) or only loaded (False)
	# @param custom If True, fields are added to those existing in the model
	def add_view(self, arch, fields, display=False, custom=False, toolbar={}):
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
		view, on_write = ViewFactory.create(self, self.resource, dom, self.fields, toolbar=toolbar)
		self.setOnWrite( on_write )

		self.views.append(view)

		if display:
			self.__current_view = len(self.views) - 1
			self.current_view.display(self.current_model, self.models)
			self.setView(view)
		return view

	def readOnly(self):
		return self.current_view.readOnly

	def new(self, default=True):
		if self.current_view and self.current_view.view_type == 'tree' \
				and self.current_view.readOnly:
			self.switchView()
		model = self.models.newModel(default, self.domain, self.context)

		if (not self.current_view) or self.current_view.model_add_new or self.create_new:
			self.models.addModel(model, self.new_model_position())

		if self.current_view:
			self.current_view.reset()

		self.current_model = model
		#self.current_model.setValidate()
		self.display()
		return self.current_model

	def new_model_position(self):
		position = -1
		if self.current_view and self.current_view.view_type =='tree' \
			    and self.current_view.readOnly():
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
			self.current_view.set_cursor()
			return False
		
		if self.current_view.view_type == 'tree':
			for model in self.models.models:
				if model.isModified():
					if model.validate():
						id = model.save(reload=True)
					else:
						self.current_model = model
						self.display()
						self.current_view.set_cursor()
						return False
			self.display()
			self.current_view.set_cursor()

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
		id = False
		if self.current_model:
			id = self.current_model.id
			idx = self.models.models.index(self.current_model)
			self.models.remove(self.current_model)
			if self.models.models:
				idx = min(idx, len(self.models.models)-1)
				self.current_model = self.models.models[idx]
			else:
				self.current_model = None
			if unlink and id:
				self.rpc.unlink([id])
			self.display()
		return id

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
