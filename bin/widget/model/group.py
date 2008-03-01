##############################################################################
#
# Copyright (c) 2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id$
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

from PyQt4.QtCore import *

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
class ModelRecordGroup(QObject):
	# If fields is None, all fields are loaded. This means an extra query (fields_get) to the server. Use with care.
	# If you don't know the numbers of fields you'll use, but want some ids to be loaded use fields={}
	# parent is only used if this ModelRecordGroup serves as a relation to another model. Otherwise it's None.
	def __init__(self, resource, fields = None, ids=[], parent=None, context={}):
		QObject.__init__(self)
		self.parent = parent
		self._context = context
		self._context.update(rpc.session.context)
		self.resource = resource
		self.rpc = RPCProxy(resource)
		if fields == None:
			self.fields = {}
		else:
			self.fields = fields
		self.mfields = {}
		self.mfields_load(self.fields.keys())

		self.models = ModelList(self)

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
		model_idx = self.models.index(self[edited_id])
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

		c = rpc.session.context.copy()
		c.update(self.context)
		values = self.rpc.read(ids, self.fields.keys(), c)
		if not values:
			return False
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
					self[id].set(v, signal=False)

		# Set defaults
		if len(new) and len(to_add):
			values = self.rpc.default_get(to_add, self.context)
			for t in to_add:
				if t not in values:
					values[t] = False
			for mod in new:
				mod.setDefaults(values)

	## @brief Returns the number of models in this group.
	def count(self):
		return len(self.models)

	def __iter__(self):
		return iter(self.models)

	## @brief Returns the model with id 'id'. You can use [] instead.
	def modelById(self, id):
		for model in self.models:
			if model.id == id:
				return model

	__getitem__ = modelById

# vim:noexpandtab:
