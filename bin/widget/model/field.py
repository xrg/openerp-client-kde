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

from PyQt4.QtCore import *
from rpc import RPCProxy
import rpc

try:
	from sets import Set as set
except ImportError:
	pass


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
		return model.expr_eval(dom)

	def context(self, model, check_load=True, eval=True):
		context = {}
		context.update(self.parent.context)
		field_context_str = self.attrs.get('context', '{}') or '{}'
		if eval:
			field_context = model.expr_eval('dict(%s)' % field_context_str, check_load=check_load)
			context.update(field_context)
		return context

	## Checks if the current value is valid and sets stateAttributes on the model.
	# 
	# Here it's checked if the field is required but is empty.
	def validate(self, model):
		ok = True
		if bool(int(self.stateAttributes(model).get('required', 0))):
			if not model.values[self.name]:
				ok=False
		self.stateAttributes(model)['valid'] = ok
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

	def setStateAttributes(self, model, state='draft'):
		state_changes = dict(self.attrs.get('states',{}).get(state,[]))
		for key in ('readonly', 'required'):
			if key in state_changes:
				self.stateAttributes(model)[key] = state_changes[key]
			else:
				self.stateAttributes(model)[key] = self.attrs[key]
		if 'value' in state_changes:
			self.set(model, value, test_state=False, modified=True)
	
	def stateAttributes(self, model):
		if self.name not in model.state_attrs:
			model.state_attrs[self.name] = self.attrs.copy()
		return model.state_attrs[self.name]

class SelectionField(StringField):
	def set(self, model, value, test_state=True, modified=False):
		if value in [sel[0] for sel in self.attrs['selection']]:
			super(SelectionField, self).set(model, value, test_state, modified)

class FloatField(StringField):
	def validate(self, model):
		self.stateAttributes(model)['valid'] = True
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
		self.stateAttributes(model)['valid'] = True
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
			rpc2 = RPCProxy(self.attrs['relation'])
			result = rpc2.name_get([value], rpc.session.context)
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

class ManyToManyField(StringField):
	# internal = [id]

	def create(self, model):
		return []

	def get(self, model, check_load=True, readonly=True, modified=False):
		return [(6, 0, model.values[self.name] or [])]

	def get_client(self, model):
		print "get_client: ", model.values[self.name] or []
		return model.values[self.name] or []

	def set(self, model, value, test_state=False, modified=False):
		model.values[self.name] = value or []
		if modified:
			model.modified = True
			model.modified_fields.setdefault(self.name)

	def set_client(self, model, value, test_state=False):
		internal = model.values[self.name]
		self.set(model, value, test_state, modified=False)
		if set(internal) != set(value):
			self.changed(model)

	def default(self, model):
		return self.get_client(model)


class OneToManyField(StringField):
	def create(self, model):
		from widget.model.group import ModelRecordGroup
		mod = ModelRecordGroup(resource=self.attrs['relation'], fields={}, parent=model, context=self.context(model, eval=False))
		self.connect( mod, SIGNAL('modelChanged( PyQt_PyObject )'), self._modelChanged )
		return mod

	def _modelChanged(self, model):
		self.changed(model.parent)

	def get_client(self, model):
		return model.values[self.name]

	def get(self, model, check_load=True, readonly=True, modified=False):
		if not model.values[self.name]:
			return []
		result = []
		for model2 in model.values[self.name].models:
			if (modified and not model2.isModified()) or (not model2.id and not model2.isModified()):
				continue
			if model2.id:
				result.append((1,model2.id, model2.get(check_load=check_load, get_readonly=readonly)))
			else:
				result.append((0,0, model2.get(check_load=check_load, get_readonly=readonly)))
		for id in model.values[self.name].model_removed:
			result.append((2,id, False))
		return result

	def set(self, model, value, test_state=False, modified=False):
		from widget.model.group import ModelRecordGroup
		mod = ModelRecordGroup(resource=self.attrs['relation'], fields={}, parent=model, context=self.context(model, False))
		self.connect( mod, SIGNAL('modelChanged( PyQt_PyObject )'), self._modelChanged )
		model.values[self.name] = mod
		model.values[self.name].pre_load(value, display=False)

	def set_client(self, model, value, test_state=False):
		self.set(model, value, test_state=test_state)
		model.changed()

	def setDefault(self, model, value):
		from widget.model.group import ModelRecordGroup
		fields = {}
		if value and len(value):
			context = self.context(model)
			rpc2 = RPCProxy(self.attrs['relation'])
			fields = rpc2.fields_get(value[0].keys(), context)

		model.values[self.name] = ModelRecordGroup(resource=self.attrs['relation'], fields=fields, parent=model)
		self.connect( model.values[self.name], SIGNAL('modelChanged( PyQt_PyObject )'), self._modelChanged )
		mod=None
		for record in (value or []):
			mod = model.values[self.name].model_new(default=False)
			mod.setDefault(record)
			model.values[self.name].model_add(mod)
		model.values[self.name].current_model = mod
		return True

	def default(self, model):
		res = map(lambda x: x.defaults(), model.values[self.name].models or [])
		return res

	def validate(self, model):
		ok = True
		for model2 in model.values[self.name].models:
			if not model2.validate():
				if not model2.isModified():
					model.values[self.name].models.remove(model2)
				else:
					ok = False
		if not super(OneToManyField, self).validate(model):
			ok = False
		self.stateAttributes(model)['valid'] = ok
		return ok

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
		rpc2 = RPCProxy(ref_model)
		result = rpc2.name_get([id], rpc.session.context)
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
