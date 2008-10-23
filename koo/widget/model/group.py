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

from rpc import RPCProxy
import rpc
from record import ModelRecord
import field
from common import options

from PyQt4.QtCore import *
from PyQt4.QtGui import *

try:
	a = set()
except NameError:
	from sets import Set as set

class ModelList(list):
	def __init__(self, recordGroup):
		super(ModelList, self).__init__()
		self.lock_signal = False
		self.recordGroup = recordGroup 

	def insert(self, pos, obj):
		super(ModelList, self).insert(pos, obj)
		if not self.lock_signal:
			self.recordGroup.emit(SIGNAL('recordChanged(QString,int)'), 'record-added', pos)

	def append(self, obj):
		super(ModelList, self).append(obj)
		if not self.lock_signal:
			self.recordGroup.emit(SIGNAL('recordChanged(QString,int)'), 'record-added', -1)

	def remove(self, obj):
		idx = self.index(obj)
		super(ModelList, self).remove(obj)
		if not self.lock_signal:
			self.recordGroup.emit(SIGNAL('recordChanged(QString,int)'), 'record-removed', idx)
	
	def clear(self):
		for obj in range(len(self)):
			self.pop()
			if not self.lock_signal:
				self.recordGroup.emit(SIGNAL('recordChanged(QString,int)'), 'record-removed', len(self))

	def __setitem__(self, key, value):
		super(ModelList, self).__setitem__(key, value)
		if not self.lock_signal:
			self.recordGroup.emit(SIGNAL('recordChanged(QString,int)'), 'record-changed', key)

## @brief The ModelRecordGroup class enables manages a list of objects (models).
# 
# Provides functions for loading, storing and creating new objects of the same type.
# The 'fields' property stores a dictionary of dictionaries, each of which contains 
# function about a field. This information includes the data type ('type'), its name
# ('name') and other attributes. The 'mfields' property stores the classes responsible
# for managing the values which are finally stored on the 'values' dictionary in the
# Model
#
# The model can also be sorted by any of it's fields. Two sorting methods are provided:
# SortVisibleItems and SortAllItems. SortVisibleItems is usually faster for a small
# number of elements as sorting is handled on the client side, but only those loaded
# are considered in the sorting. SortAllItems, sorts items in the server so all items
# are considered. Although this would cost a lot when there are thousands of items, 
# only some of them are loaded and the rest are loaded on demand.
class ModelRecordGroup(QObject):

	SortVisibleItems = 1
	SortAllItems = 2

	# If fields is None, all fields are loaded. This means an extra query (fields_get) to the server. Use with care.
	# If you don't know the numbers of fields you'll use, but want some ids to be loaded use fields={}
	# parent is only used if this ModelRecordGroup serves as a relation to another model. Otherwise it's None.
	def __init__(self, resource, fields = None, ids=[], parent=None, context={}):
		QObject.__init__(self)
		self.parent = parent
		self._context = context
		self._context.update(rpc.session.context)
		self.resource = resource
		self.limit = options.options.get( 'limit', 80 )
		self.rpc = RPCProxy(resource)
		if fields == None:
			self.fields = {}
		else:
			self.fields = fields
		self.mfields = {}
		self.mfields_load(self.fields.keys())

		self.models = ModelList(self)
		
		self.sortedField = None
		self.sortedRelatedIds = []
		self.sortedOrder = None
		self.updated = False
		self._domain = []
		self._filter = []

		#self._sortMode = self.SortVisibleItems
		if options.options['sort_mode'] == 'visible_items':
			self._sortMode = self.SortVisibleItems
		else:
			self._sortMode = self.SortAllItems

		self.load(ids)
		self.model_removed = []
		self.on_write = ''


	## @brief Creates the entries in 'mfields' for each key of the 'fkeys' list.
	def mfields_load(self, fkeys):
		for fname in fkeys:
			fvalue = self.fields[fname]
			fvalue['name'] = fname
			self.mfields[fname] = field.FieldFactory.create( fvalue['type'], self, fvalue )

	## @brief Saves all the models. 
	#
	# Note that there will be one request to the server per modified or 
	# created model.
	def save(self):
		for model in self.models:
			saved = model.save()
			# TODO: Ensure this is the right place to call
			# this function. It seems that ModelRecord.save()
			# would be more appropiate, as otherwise storing
			# a single model won't trigger the 'on_write' 
			# function on the server.
			self.written(saved)

	## @brief This function executes the 'on_write' function in the server.
	#
	# If there is a 'on_write' function associated with the model type handled by 
	# this model group it will be executed. 'edited_id' should provide the 
	# id of the just saved model.
	#
	# This functionality is provided here instead of on the model because
	# the remote function might update some other models, and they need to
	# be (re)loaded.
	def written(self, edited_id):
		if not self.on_write:
			return
		new_ids = getattr(self.rpc, self.on_write)(edited_id, self.context)
		model_idx = self.models.index(self.recordById(edited_id))
		result = False
		for id in new_ids:
			cont = False
			for m in self.models:
				if m.id == id:
					cont = True
					m.reload()
			if cont:
				continue
			newmod = ModelRecord(self.resource, id, parent=self.parent, group=self)
			newmod.reload()
			if not result:
				result = newmod
			new_index = min(model_idx, len(self.models)-1)
			self.addModel(newmod, new_index)
		return result
	
	## @brief Creates as many records as len(ids) with the id[x] as id.
	#
	# 'ids' needs to be a list of identifiers. addFields can be used later to 
	# load the necessary fields for each record.
	def pre_load(self, ids, display=True):
		if not ids:
			return True
		if len(ids)>10:
			self.models.lock_signal = True
		for id in ids:
			newmod = ModelRecord(self.resource, id, parent=self.parent, group=self)
			self.addModel(newmod)
			if display:
				self.emit(SIGNAL('modelChanged( PyQt_PyObject )'), newmod)
		if len(ids)>10:
			self.models.lock_signal = False
			self.emit(SIGNAL('recordCleared()'))
		return True

	## @brief Adds a list of models as specified by 'values'.
	#
	# 'values' has to be a list of dictionaries, each of which containing fields
	# names -> values. At least key 'id' needs to be in all dictionaries.
	def load_for(self, values):
		if len(values)>10:
			self.models.lock_signal = True

		for value in values:
			newmod = ModelRecord(self.resource, value['id'], parent=self.parent, group=self)
			newmod.set(value)
			self.models.append(newmod)
			self.connect(newmod, SIGNAL('recordChanged( PyQt_PyObject )'), self._record_changed )

		if len(values)>10:
			self.models.lock_signal = False
			self.emit(SIGNAL('recordCleared()'))
	
	## @brief Loads the list of ids in this group.
	def load(self, ids, display=True):
		if not ids:
			return True

		if not self.fields:
			return self.pre_load(ids, display)

		if self._sortMode == self.SortAllItems:
			self.pre_load( ids, False )
			queryIds = ids[0:self.limit]
		else:
			queryIds = ids

		if None in queryIds:
			queryIds.remove( None )
		c = rpc.session.context.copy()
		c.update(self.context)
		values = self.rpc.read(queryIds, self.fields.keys(), c)
		if not values:
			return False

		if self._sortMode == self.SortAllItems:
			#if not self.models:
			# If nothing else was loaded, we sort the fields in the order given
			# by 'ids' or 'self.sortedRedlatedIds' when appropiate.
			if self.sortedRelatedIds:
				# This treats the case when the sorted field is a many2one
				nulls = []
				for y in values:
					if type(y[self.sortedField]) != list:
						nulls.append( y )
				vals = []
				for x in self.sortedRelatedIds:
					for y in values:
						value = y[self.sortedField]
						if type(value) == list and y[self.sortedField][0] == x:
							vals.append( y )
							# Don't break, there can be duplicates
				if self.sortedOrder == Qt.AscendingOrder:
					vals = nulls + vals
				else:
					vals = vals + nulls
			else:
				# This treats the case when the sorted field is a non-relation field
				#vals = sorted( values, key=lambda x: ids.index(x['id']) )
				for v in values:
					id = v['id']
					self.recordById(id).set(v, signal=False)
		else:
			self.load_for(values)
		return True

	## @brief Clears the list of models. It doesn't remove them.
	def clear(self):
		self.models.clear()
		self.model_removed = []
	
	## @brief Returns a copy of the current context
	def getContext(self):
		ctx = {}
		ctx.update(self._context)
		return ctx
	context = property(getContext)

	## @brief Adds a model to the list
	def addModel(self, model, position=-1):
		if not model.mgroup is self:
			fields = {}
			for mf in model.mgroup.fields:
				fields[model.mgroup.fields[mf]['name']] = model.mgroup.fields[mf]
			self.addFields(fields)
			model.mgroup.addFields(self.fields)
			model.mgroup = self

		if position==-1:
			self.models.append(model)
		else:
			self.models.insert(position, model)
		model.parent = self.parent
		self.connect(model, SIGNAL('recordChanged( PyQt_PyObject )'), self._record_changed)
		return model

	## @brief Adds a new model to the model group
	#
	# If 'default' is true, the model is filled in with default values. 
	# 'domain' and 'context' are only used if default is true.
	def newModel(self, default=True, domain=[], context={}):
		newmod = ModelRecord(self.resource, None, group=self, 
					   parent=self.parent, new=True)
		self.connect(newmod, SIGNAL('recordChanged( PyQt_PyObject )'), self._record_changed)
		if default:
			ctx=context.copy()
			ctx.update(self.context)
			newmod.fillWithDefaults(domain, ctx)
		self.emit(SIGNAL('modelChanged( PyQt_PyObject )'), newmod)
		return newmod
	
	def _record_changed(self, model):
		self.emit(SIGNAL('modelChanged( PyQt_PyObject )'), model)

	## @brief Removes a model from the model group but not from the server.
	#
	# If the model doesn't exist it will ignore it silently.
	def remove(self, model):
		try:
			idx = self.models.index(model)
			if self.models[idx].id:
				self.model_removed.append(self.models[idx].id)
			if model.parent:
				model.parent.modified = True
			self.models.remove(self.models[idx])
		except:
			pass

	## @brief Adds the specified fields to the model group
	#
	# Note that it updates 'fields' and 'mfields' in the group
	# and creates the necessary entries in the 'values' property of 
	# all the models. 'fields' is a dict of dicts as typically returned by 
	# the server.
	def addCustomFields(self, fields):
		to_add = []
		for f in fields.keys():
			if not f in self.fields:
				self.fields[f] = fields[f]
				self.fields[f]['name'] = f
				to_add.append(f)
			else:
				self.fields[f].update(fields[f])
		self.mfields_load(to_add)
		for fname in to_add:
			for m in self.models:
				m.values[fname] = self.mfields[fname].create(m)
		return to_add

	## @brief Adds the specified fields and loads the necessary ones from the 
	# server.
	#
	# 'fields' is a dict of dicts as typically returned by the server.
	def addFields(self, fields):
		to_add = self.addCustomFields(fields)
		if not len(self.models):
			return True

		old = []
		new = []
		for model in self.models:
			if model.id:
				if model._loaded:
					old.append(model.id)
			else:
				new.append(model)

		# Update existing models
		if len(old) and len(to_add):
			c = rpc.session.context.copy()
			c.update(self.context)
			values = self.rpc.read(old, to_add, c)
			if values:
				for v in values:
					id = v['id']
					if 'id' not in to_add:
						del v['id']
					self.recordById(id).set(v, signal=False)

		# Set defaults
		if len(new) and len(to_add):
			values = self.rpc.default_get(to_add, self.context)
			for t in to_add:
				if t not in values:
					values[t] = False
			for mod in new:
				mod.setDefaults(values)

	def ensureAllLoaded(self):
		ids = [x.id for x in self.models if not x._loaded]
		c = rpc.session.context.copy()
		c.update(self.context)
		values = self.rpc.read( ids, self.fields.keys(), c )
		if values:
			for v in values:
				self.recordById( v['id'] ).set(v, signal=False)

	## @brief Returns the number of models in this group.
	def count(self):
		return len(self.models)

	def __iter__(self):
		self.ensureAllLoaded()
		return iter(self.models)

	## @brief Returns the model with id 'id'. You can use [] instead.
	# Note that it will check if the model is loaded and load it if not.
	def modelById(self, id):
		for model in self.models:
			if model.id == id:
				self.ensureModelLoaded(model)
				return model
	__getitem__ = modelById

	def modelByRow(self, row):
		model = self.models[row]
		if model._loaded == False:
			self.ensureModelLoaded(model)
		return model

	# Returns whether model is in the list of LOADED models
	# If we use 'model in model_group' then it will try to
	# load all models and if one of the models has id False
	# an error will be fired.
	def modelExists(self, model):
		return model in self.models

	## @brief Returns the model with id 'id'. You can use [] instead.
	# Note that it will return the record (model) but won't try to load it.
	def recordById(self, id):
		for model in self.models:
			if model.id == id:
				return model

	def ensureModelLoaded(self, model):
		if model._loaded:
			return 

		c = rpc.session.context.copy()
		c.update(self.context)
		ids = [x.id for x in self.models]
		pos = ids.index(model.id) / self.limit

		queryIds = ids[pos * self.limit: pos * self.limit + self.limit]
		if None in queryIds:
			queryIds.remove( None )
		values = self.rpc.read(queryIds, self.fields.keys(), c)
		if not values:
			return False

		# This treats the case when the sorted field is a non-relation field
		for v in values:
			id = v['id']
			self.recordById(id).set(v, signal=False)

	def setDomain(self, value):
		if value == None:
			self._domain = []
		else:
			self._domain = value
	
	def domain(self):
		return self._domain

	def setFilter(self, value):
		if value == None:
			self._filter = []
		else:
			self._filter = value
	
	def filter(self):
		return self._filter

	## @brief Reload the model group with current selected sort field, order, domain and filter
	def update(self):
		#f = self.sortedField
		#self.sortedField = None
		## Make it reload again
		self.updated = False
		self.sort( self.sortedField, self.sortedOrder )

	## @brief Sorts the model by the given field name.
	def sort(self, field, order):
		if self._sortMode == self.SortAllItems:
			self.sortAll( field, order )
		else:
			self.sortVisible( field, order )

	def sortAll(self, field, order):
		if self.updated and field == self.sortedField and order == self.sortedOrder:
			return
		if not field in self.fields.keys():
			# If the field doesn't exist use default sorting. Usually this will
			# happen when we update and haven't selected a field to sort by.
			ids = self.rpc.search( self._domain + self._filter )
			self.sortedRelatedIds = []
		else:
			type = self.fields[field]['type']
			if type == 'one2many' or type == 'many2many':
				# We're not able to sort 2many fields
				return

			# A lot of the work done here should be done on the server by core TinyERP
			# functions. This means this runs slower than it should due to network and
			# serialization latency. Even more, we lack some information to make it 
			# work well.

			if type == 'many2one':
				# In the many2one case, we sort all records in the related table 
				# There's a bug here, as we consider 'name' the field that will be shown.
				# in some cases this field doesn't exist.
				orderby = 'name '
				if order == Qt.AscendingOrder:
					orderby += 'ASC'
				else:
					orderby += 'DESC'
				try:
					# Use call to catch exceptions
					self.sortedRelatedIds = rpc.session.call('/object', 'execute', self.fields[field]['relation'], 'search', [], 0, 0, orderby )
				except:
					# Maybe name field doesn't exist :(
					# Use default order
					self.sortedRelatedIds = rpc.session.call('/object', 'execute', self.fields[field]['relation'], 'search', [], 0, 0 )
					
				ids = self.rpc.search( self._domain + self._filter )
			else:
				orderby = field + " "
				if order == Qt.AscendingOrder:
					orderby += "ASC"
				else:
					orderby += "DESC"
				try:
					# Use call to catch exceptions
					ids = rpc.session.call('/object', 'execute', self.resource, 'search', self._domain + self._filter, 0, 0, orderby )
				except:
					# In functional fields not stored in the database this will
					# cause an exceptioin :(
					# Use default order
					ids = rpc.session.call('/object', 'execute', self.resource, 'search', self._domain + self._filter, 0, 0 )
				self.sortedRelatedIds = []

		# We set this fields in the end in case some exceptions where fired 
		# in previous steps.
		self.sortedField = field
		self.sortedOrder = order
		self.updated = True

		self.clear()
		# The load function will be in charge of loading and sorting elements
		self.load( ids )

	def sortVisible(self, field, order):
		if self.updated and field == self.sortedField and order == self.sortedOrder:
			return

		if not self.updated:
			ids = rpc.session.call('/object', 'execute', self.resource, 'search', self._domain + self._filter, 0, self.limit )
			self.clear()
			self.load( ids )
		
		if not field in self.fields:
			return

		if field != self.sortedField:
			# Sort only if last sorted field was different than current

			# We need this function here as we use the 'field' variable
			def ignoreCase(model):
				v = model.value(field)
				if isinstance(v, unicode) or isinstance(v, str):
					return v.lower()
				else:
					return v

			type = self.fields[field]['type']
			if type == 'one2many' or type == 'many2many':
				self.models.sort( key=lambda x: len(x.value(field).models) )
			else:
				self.models.sort( key=ignoreCase )
			if order == Qt.DescendingOrder:
				self.models.reverse()
		else:
			# If we're only reversing the order, then reverse simply reverse
			if order != self.sortedOrder:
				self.models.reverse()

		self.sortedField = field
		self.sortedOrder = order
		self.updated = True
		self.emit(SIGNAL('recordCleared()'))

# vim:noexpandtab:
