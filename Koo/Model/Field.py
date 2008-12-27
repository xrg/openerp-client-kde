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

from PyQt4.QtCore import *
from Koo.Rpc import RpcProxy, Rpc
from Koo import Rpc
import base64


class StringField(QObject):
	def __init__(self, parent, attrs):
		QObject.__init__(self)
		self.parent = parent
		self.attrs = attrs
		self.name = attrs['name']
		self.internal = False

	## This function is in charge of execting "on_change" and
	# "change_defalt" events and setting the appropiate model 
	# as modified.
	def changed(self, model):
		model.modified = True
		model.modified_fields.setdefault(self.name)
		model.changed()
		if self.attrs.get('on_change',False):
			model.callOnChange(self.attrs['on_change'])
		if self.attrs.get('change_default', False):
			model.setConditionalDefaults(self.name, self.get(model))

	def domain(self, model):
		dom = self.attrs.get('domain', '[]')
		return model.evaluateExpression(dom)

	def context(self, model, check_load=True, eval=True):
		context = {}
		context.update( self.parent.context() )
		field_context_str = self.attrs.get('context', '{}') or '{}'
		if eval:
			field_context = model.evaluateExpression('dict(%s)' % field_context_str, check_load=check_load)
			context.update(field_context)
		return context

	## Checks if the current value is valid and sets stateAttributes on the model.
	# 
	# Here it's checked if the field is required but is empty.
	def validate(self, model):
		ok = True
		# We ensure that the field is read-write. In some cases there might be 
		# forms in which a readonly field is marked as required. For example,
		# banks some fields inside partner change readonlyness depending on the 
		# value of a selection field. 
		if not self.stateAttributes(model).get('readonly', False):
			if bool(int(self.stateAttributes(model).get('required', 0))):
				if not model.values[self.name]:
					ok=False
		model.setFieldValid( self.name, ok )
		return ok

	## Stores the value from the server
	def set(self, model, value, test_state=True, modified=False):
		model.values[self.name] = value
		if modified:
			model.modified = True
			model.modified_fields.setdefault(self.name)
		return True

	## Return the value to write to the server
	def get(self, model, check_load=True, readonly=True, modified=False):
		return model.values.get(self.name, False) 

	## Stores the value for the client widget
	def set_client(self, model, value, test_state=True):
		internal = model.values.get(self.name, False)
		self.set(model, value, test_state)
		if (internal or False) != (model.values.get(self.name,False) or False):
			self.changed(model)

	## Returns the value for the client widget
	def get_client(self, model):
		return model.values.get(self.name, False)

	def setDefault(self, model, value):
		return self.set(model, value)

	def default(self, model):
		return self.get(model)

	def create(self, model):
		return False

	def stateAttributes(self, model):
		if self.name not in model.state_attrs:
			model.state_attrs[self.name] = self.attrs.copy()
		return model.state_attrs[self.name]

class BinaryField(StringField):
	def set(self, model, value, test_state=True, modified=False):
		model.values[self.name] = None
		if modified:
			model.modified = True
			model.modified_fields.setdefault(self.name)
		return True

	def set_client(self, model, value, test_state=True):
		internal = model.values.get(self.name, False)
		model.values[self.name] = value
		if (internal or False) != model.values[self.name]:
			self.changed(model)

	def get(self, model, check_load=True, readonly=True, modified=False):
		value = self.get_client(model)
		if value:
			value = base64.encodestring(value)
		return value

	def get_client(self, model):
		if model.values[self.name] is None and model.id:
			c = Rpc.session.context.copy()
			c.update(model.context())
			value = model.rpc.read([model.id], [self.name], c)[0][self.name]
			if value:
				model.values[self.name] = base64.decodestring(value)
		return model.values[self.name]

class SelectionField(StringField):
	def set(self, model, value, test_state=True, modified=False):
		if value in [sel[0] for sel in self.attrs['selection']]:
			super(SelectionField, self).set(model, value, test_state, modified)

class FloatField(StringField):
	def validate(self, model):
		model.setFieldValid( self.name, True )
		return True

	def set_client(self, model, value, test_state=True):
		internal = model.values[self.name]
		self.set(model, value, test_state)
		if abs(float(internal or 0.0) - float(model.values[self.name] or 0.0)) >= (10.0**(-int(self.attrs.get('digits', (12,4))[1]))):
			if not self.stateAttributes(model).get('readonly', False):
				self.changed(model)

class IntegerField(StringField):

	def get(self, model, check_load=True, readonly=True, modified=False):
		return model.values.get(self.name, 0) or 0

	def get_client(self, model):
		return model.values[self.name] or 0

	def validate(self, model):
		model.setFieldValid( self.name, True )
		return True


class ManyToOneField(StringField):
		
	#internal = (id, name)

	def create(self, model):
		return False

	def get(self, model, check_load=True, readonly=True, modified=False):
		if model.values[self.name]:
			return model.values[self.name][0] or False
		return False

	def get_client(self, model):
		if model.values[self.name]:
			return model.values[self.name][1]
		return False

	def set(self, model, value, test_state=False, modified=False):
		if value and isinstance(value, (int, str, unicode, long)):
			Rpc2 = RpcProxy(self.attrs['relation'])
			result = Rpc2.name_get([value], Rpc.session.context)

			# In some very rare cases we may get an empty
			# list from the server so we just check it before
			# trying to store result[0]
			if result:
				model.values[self.name] = result[0]
		else:
			model.values[self.name] = value
		if modified:
			model.modified = True
			model.modified_fields.setdefault(self.name)

	def set_client(self, model, value, test_state=False):
		internal = model.values[self.name]
		self.set(model, value, test_state)
		if internal != model.values[self.name]:
			self.changed(model)

# This is the base class for ManyToManyField and OneToManyField
# The only difference between these classes is the 'get()' method.
# In the case of ManyToMany we always return all elements because
# it only stores the relation between two models which already exist.
# In the case of OneToMany we only return those objects that have 
# been modified because the pointed object stores the relation to the
# parent.
class ToManyField(StringField):
	def create(self, model):
		from Koo.Model.Group import ModelRecordGroup
		mod = ModelRecordGroup(resource=self.attrs['relation'], fields={}, parent=model, context=self.context(model, eval=False))
		self.connect( mod, SIGNAL('modelChanged( PyQt_PyObject )'), self._modelChanged )
		return mod

	def _modelChanged(self, model):
		self.changed(model.parent)

	def get_client(self, model):
		return model.values[self.name]

	def get(self, model, check_load=True, readonly=True, modified=False):
		pass

	def set(self, model, value, test_state=False, modified=False):
		from Koo.Model.Group import ModelRecordGroup
		mod = ModelRecordGroup(resource=self.attrs['relation'], fields={}, parent=model, context=self.context(model, False))
		self.connect( mod, SIGNAL('modelChanged( PyQt_PyObject )'), self._modelChanged )
		mod.setDomain( [('id','in',value)] )
		mod.preload(value)
		model.values[self.name] = mod

	def set_client(self, model, value, test_state=False):
		self.set(model, value, test_state=test_state)
		self.changed(model)

	def setDefault(self, model, value):
		from Koo.Model.Group import ModelRecordGroup
		fields = {}
		if value and len(value):
			context = self.context(model)
			Rpc2 = RpcProxy(self.attrs['relation'])
			fields = Rpc2.fields_get(value[0].keys(), context)

		model.values[self.name] = ModelRecordGroup(resource=self.attrs['relation'], fields=fields, parent=model)
		self.connect( model.values[self.name], SIGNAL('modelChanged( PyQt_PyObject )'), self._modelChanged )
		mod=None
		for record in (value or []):
			mod = model.values[self.name].model_new(default=False)
			mod.setDefault(record)
			model.values[self.name].model_add(mod)
		return True

	def default(self, model):
		return [ x.defaults() for x in model.values[self.name].records ]

	def validate(self, model):
		ok = True
		for model2 in model.values[self.name].records:
			if not model2.validate():
				if not model2.isModified():
					model.values[self.name].records.remove(model2)
				else:
					ok = False
		if not super(ToManyField, self).validate(model):
			ok = False
		model.setFieldValid( self.name, ok )
		return ok

class OneToManyField(ToManyField):
	def get(self, model, check_load=True, readonly=True, modified=False):
		if not model.values[self.name]:
			return []
		result = []
		for model2 in model.values[self.name].records:
			if (modified and not model2.isModified()) or (not model2.id and not model2.isModified()):
				continue
			if model2.id:
				result.append((1,model2.id, model2.get(check_load=check_load, get_readonly=readonly)))
			else:
				result.append((0,0, model2.get(check_load=check_load, get_readonly=readonly)))
		for id in model.values[self.name].model_removed:
			result.append((2,id, False))
		return result

class ManyToManyField(ToManyField):
	def get(self, model, check_load=True, readonly=True, modified=False):
		if not model.values[self.name]:
			return []
		return [(6, 0, [x.id for x in model.values[self.name].records])]

class ReferenceField(StringField):
	def get_client(self, model):
		if model.values[self.name]:
			return model.values[self.name]
		return False

	def get(self, model, check_load=True, readonly=True, modified=False):
		if model.values[self.name]:
			return '%s,%d' % (model.values[self.name][0], model.values[self.name][1][0])
		return False

	def set_client(self, model, value):
		internal = model.values[self.name]
		model.values[self.name] = value
		if (internal or False) != (model.values[self.name] or False):
			self.changed(model)

	def set(self, model, value, test_state=False, modified=False):
		if not value:
			model.values[self.name] = False
			return
		ref_model, id = value.split(',')
		Rpc2 = RpcProxy(ref_model)
		result = Rpc2.name_get([id], Rpc.session.context)
		if result:
			model.values[self.name] = ref_model, result[0]
		else:
			model.values[self.name] = False
		if modified:
			model.modified = True
			model.modified_fields.setdefault(self.name)


## @brief The FieldFactory class provides a means of creating the appropiate object
#  to handle a given field type. 
#
#  By default some classes exist for many file types
#  but if you create new types or want to replace current implementations you can
#  do it too.
class FieldFactory:
	## The types property holds the class that will be called whenever a new
	#  object has to be created for a given field type.
	#  By default there's a number of field types but new ones can be easily 
	#  created or existing ones replaced.
	types = {
		'char' : StringField,
		'binary' : BinaryField,
		'image' : BinaryField,
		'float_time': FloatField,
		'integer' : IntegerField,
		'float' : FloatField,
		'many2one' : ManyToOneField,
		'many2many' : ManyToManyField,
		'one2many' : OneToManyField,
		'reference' : ReferenceField,
		'selection': SelectionField,
		'boolean': IntegerField,
	}

	## This function creates a new instance of the appropiate class
	# for the given field type.
	@staticmethod
	def create(type, parent, attributes):
		if type in FieldFactory.types:
			return FieldFactory.types[type]( parent, attributes )
		else:
			return FieldFactory.types['char']( parent, attributes )

# vim:noexpandtab:
