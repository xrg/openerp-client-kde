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

import re
import time
import exceptions
from Koo import Rpc
from Koo.Rpc import RpcProxy
from Field import ToManyField
import gettext
import traceback

from PyQt4.QtCore import *

class EvalEnvironment(object):
	def __init__(self, parent):
		self.parent = parent

	def __getattr__(self, item):
		if item=='parent' and self.parent.parent:
			return EvalEnvironment(self.parent.parent)
		if item=="current_date":
			return time.strftime('%Y-%m-%d')
		if item=="time":
			return time
		return self.parent.get(includeid=True)[item]


# We inherit QObject as we'll be using signals & slots
class ModelRecord(QObject):
	def __init__(self, resource, id, group=None, parent=None, new=False ):
		QObject.__init__(self)
		self.resource = resource
		self.rpc = RpcProxy(self.resource)
		self.id = id
		self._loaded = False
		self.parent = parent
		self.mgroup = group
		self.values = {}
		self.state_attrs = {}
		self.modified = False
		self.modified_fields = {}
		self.invalidFields = []
		self.read_time = time.time()
		for key,val in self.mgroup.mfields.items():
			self.values[key] = val.create(self)
			if (new and val.attrs['type']=='one2many') and (val.attrs.get('mode','tree,form').startswith('form')):
				mod = self.values[key].newModel()
				self.values[key].addModel(mod)

	def _getModified(self):
		return self._modified
	def _setModified(self,value):
		self._modified = value
	modified=property(_getModified,_setModified)

	def __getitem__(self, name):
		return self.mgroup.mfields.get(name, False)
	
	def __repr__(self):
		return '<ModelRecord %s@%s>' % (self.id, self.resource)

	# Establishes the value for a given field
	def setValue(self, fieldName, value):
		self.mgroup.mfields[fieldName].set_client(self, value)

	# Obtains the value of a given field
	def value(self, fieldName):
		return self.mgroup.mfields[fieldName].get_client(self)

	# Establishes the default value for a given field
	def setDefault(self, fieldName, value):
		self.mgroup.mfields[fieldName].set_client(self, value)

	# Obtains the default value of a given field
	def default(self, fieldName):
		#return self.mgroup.mfields[fieldName].get_client(self)
		return self.mgroup.mfields[fieldName].default(self)

	# Obtains the domain of the given field
	def domain(self, fieldName):
		return self.mgroup.mfields[fieldName].domain(self)

	# Obtains the context of the given field
	def fieldContext(self, fieldName):
		return self.mgroup.mfields[fieldName].context(self)

	# Returns whether the record has been modified or not
	def isModified(self):
		return self.modified

	def fields(self):
		return self.mgroup.mfields

	def _check_load(self):
		if not self._loaded:
			self.reload()
			return True
		return False

	def get(self, get_readonly=True, includeid=False, check_load=True, get_modifiedonly=False):
		if check_load:
			self._check_load()
		value = []
		for name, field in self.mgroup.mfields.items():
			if (get_readonly or not field.stateAttributes(self).get('readonly', False)) \
				and (not get_modifiedonly or (field.name in self.modified_fields or isinstance(field, ToManyField))):
					value.append((name, field.get(self, readonly=get_readonly,
						modified=get_modifiedonly)))
		value = dict(value)
		if includeid:
			value['id'] = self.id
		return value

	def cancel(self):
		self._loaded = False
		self.reload()

	def save(self, reload=True):
		self._check_load()
		if not self.id:
			value = self.get(get_readonly=False)
			self.id = self.rpc.create(value, self.context())
		else:
			if not self.isModified():
				return self.id
			value = self.get(get_readonly=False, get_modifiedonly=True)
			context= self.context()
			context= context.copy()
			context['read_delta']= time.time()-self.read_time
			if not Rpc.session.execute('/object', 'execute', self.resource, 'write', [self.id], value, context):
				return False
		self._loaded = False
		if reload:
			self.reload()
		return self.id

	# Used only by group.py
	def fillWithDefaults(self, domain=[], context={}):
		if len(self.mgroup.fields):
			val = self.rpc.default_get(self.mgroup.fields.keys(), context)
			for d in domain:
				if d[0] in self.mgroup.fields and d[1]=='=':
					val[d[0]]=d[2]
			self.setDefaults(val)

	def name(self):
		name = self.rpc.name_get([self.id], Rpc.session.context)[0]
		return name

	def setFieldValid(self, field, value):
		if value:
			if field in self.invalidFields:
				self.invalidFields.remove( field )
		else:
			if not field in self.invalidFields:
				self.invalidFields.append( field )

	def isFieldValid(self, field):
		if field in self.invalidFields:
			return False
		else:
			return True

	def setValidate(self):
		change = self._check_load()
		self.invalidFields = []
		for fname in self.mgroup.mfields:			
			change = change or not self.isFieldValid( fname )
			self.setFieldValid( fname, True )
		if change:
			self.emit(SIGNAL('recordChanged( PyQt_PyObject )'), self )
		return change

	def validate(self):
 		self._check_load()
 		ok = True
 		for fname in self.mgroup.mfields:
 			if not self.mgroup.mfields[fname].validate(self):
				self.setFieldValid( fname, False )
 				ok = False
			else:
				self.setFieldValid( fname, True )
 		return ok

	def context(self):
		return self.mgroup.context

	# Returns a dict with the default value of each field
	# { 'field': defaultValue }
	def defaults(self):
		self._check_load()
		value = dict([(name, field.default(self))
					  for name, field in self.mgroup.mfields.items()])
		return value

	# Sets the default values for each field from a dict
	# { 'field': defaultValue }
	def setDefaults(self, val):
		for fieldname, value in val.items():
			if fieldname not in self.mgroup.mfields:
				continue
			self.mgroup.mfields[fieldname].setDefault(self, value)
		self._loaded = True
		self.emit(SIGNAL('recordChanged( PyQt_PyObject )'), self)

	# This functions simply emits a signal indicating that
	# the model has changed. This is mainly used by fields
	# so they don't have to emit the signal, but relay in 
	# model emiting it itself.
	def changed(self):
		self.emit(SIGNAL('recordChanged( PyQt_PyObject )'), self)	

	def set(self, val, modified=False, signal=True):
		later={}
		for fieldname, value in val.items():
			if fieldname not in self.mgroup.mfields:
				continue
			if isinstance(self.mgroup.mfields[fieldname], ToManyField):
				later[fieldname]=value
				continue
			self.mgroup.mfields[fieldname].set(self, value, modified=modified)
		for fieldname, value in later.items():
			self.mgroup.mfields[fieldname].set(self, value, modified=modified)
		self._loaded = True
		self.modified = modified
		if not self.modified:
			self.modified_fields = {}
		if signal:
			self.emit(SIGNAL('recordChanged( PyQt_PyObject )'), self)

	def reload(self):
		if not self.id:
			return
		c= Rpc.session.context.copy()
		c.update(self.context())
		res = self.rpc.read([self.id], self.mgroup.mfields.keys(), c)
		if res:
			value = res[0]
			self.read_time= time.time()
			self.set(value)

	# @brief Evaluates the string expression given by dom.
	# Before passing the dom expression to Rpc.session.evaluateExpression
	# a context with 'current_date', 'time', 'context', 'active_id' and
	# 'parent' (if applies) is prepared.
	def evaluateExpression(self, dom, check_load=True):
		if not isinstance(dom, basestring):
			return dom
		if check_load:
			self._check_load()
		d = {}
		for name, mfield in self.mgroup.mfields.items():
			d[name] = mfield.get(self, check_load=check_load)

		d['current_date'] = time.strftime('%Y-%m-%d')
		d['time'] = time
		d['context'] = self.context()
		d['active_id'] = self.id
		if self.parent:
			d['parent'] = EvalEnvironment(self.parent)
		val = Rpc.session.evaluateExpression(dom, d)
		return val

	# This function is called by the field when it's changed
	# and has a 'on_change' attribute. The 'callback' parameter
	# is the function that has to be executed on the server.
	# So the function specified is called on the server whenever
	# the field changes.
	#XXX Shoud use changes of attributes (ro, ...)
	def callOnChange(self, callback):
		match = re.match('^(.*?)\((.*)\)$', callback)
		if not match:
			raise Exception, 'ERROR: Wrong on_change trigger: %s' % callback
		func_name = match.group(1)
		arg_names = [n.strip() for n in match.group(2).split(',')]
		args = [self.evaluateExpression(arg) for arg in arg_names]
		ids = self.id and [self.id] or []
		response = getattr(self.rpc, func_name)(ids, *args)
		if response:
			self.set(response.get('value', {}), modified=True)
			if 'domain' in response:
				for fieldname, value in response['domain'].items():
					if fieldname not in self.mgroup.mfields:
						continue
					self.mgroup.mfields[fieldname].attrs['domain'] = value
		self.emit( SIGNAL('recordChanged( PyQt_PyObject '), self )
	
	# This functions is called whenever a field with 'change_default'
	# attribute set to True is modified. The function sets all conditional
	# defaults to each field.
	# Conditional defaults is a mechanism by which the user can establish
	# default values on fields, depending on the value of another field (
	# the 'change_default' field). An example of this case is the zip field
	# in the partner model.
	def setConditionalDefaults(self, field, value):
		ir = RpcProxy('ir.values')
		values = ir.get('default', '%s=%s' % (field, value),
						[(self.resource, False)], False, {})
		data = {}
		for index, fname, value in values:
			data[fname] = value
		self.setDefaults(data)

