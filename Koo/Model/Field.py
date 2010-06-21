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
from Koo.Common import Numeric


class StringField(QObject):
	def __init__(self, parent, attrs):
		QObject.__init__(self)
		self.parent = parent
		self.attrs = attrs
		self.name = attrs['name']

	## This function is in charge of executing "on_change" and
	# "change_defalt" events and setting the appropiate record 
	# as modified.
	def changed(self, record):
		record.modified = True
		record.modified_fields.setdefault(self.name)
		record.changed()
		if self.attrs.get('on_change',False):
			record.callOnChange(self.attrs['on_change'])
		if self.attrs.get('change_default', False):
			record.setConditionalDefaults(self.name, self.get(record))

	def domain(self, record):
		dom = self.attrs.get('domain', '[]')
		return record.evaluateExpression(dom)

	def context(self, record, checkLoad=True, eval=True):
		context = {}
		context.update( self.parent.context() )
		if eval:
			fieldContext = self.attrs.get('context') or '{}'
			fieldContext = record.evaluateExpression('dict(%s)' % fieldContext, checkLoad=checkLoad)
			context.update(fieldContext)
		return context

	## Checks if the current value is valid and sets stateAttributes on the record.
	# 
	# Here it's checked if the field is required but is empty.
	def validate(self, record):
		ok = True
		# We ensure that the field is read-write. In some cases there might be 
		# forms in which a readonly field is marked as required. For example,
		# banks some fields inside partner change readonlyness depending on the 
		# value of a selection field. 
		if not record.isFieldReadOnly( self.name ):
			if record.isFieldRequired( self.name ):
				if not record.values[self.name]:
					ok=False
		record.setFieldValid( self.name, ok )
		return ok

	## Stores the value from the server
	def set(self, record, value, test_state=True, modified=False):
		record.values[self.name] = value
		if modified:
			record.modified = True
			record.modified_fields.setdefault(self.name)

	## Return the value to write to the server
	def get(self, record, checkLoad=True, readonly=True, modified=False):
		return record.values.get(self.name, False) 

	## Stores the value for the client widget
	def set_client(self, record, value, test_state=True):
		internal = record.values.get(self.name, False)
		self.set(record, value, test_state)
		if (internal or False) != (record.values.get(self.name,False) or False):
			self.changed(record)

	## Returns the value for the client widget
	def get_client(self, record):
		return record.values.get(self.name, False)

	def setDefault(self, record, value):
		self.set(record, value)
		# Setting defaults shouldn't by itself mark the field as changed 
		# because it's usually used in form loading. However, we're required
		# to trigger on_change events that are usually handled by the changed()
		# function.
		# 
		# Note that, although setDefault() doesn't mark the field as modified, 
		# any records that have an on_change on one of the fields filled by
		# setDefault() and that the result of on_change means modifying some
		# fields, those WILL be marked as modified.
		#
		# Maybe it would be better to set value normally (and trigger on_change
		# events there) and let Record.fillWithDefaults() be responsible for 
		# resetting all fields to not modified.
		if self.attrs.get('on_change',False):
			record.callOnChange(self.attrs['on_change'])

	def default(self, record):
		return self.get(record)

	def create(self, record):
		return False



class BinaryField(StringField):
	def __init__(self, parent, attrs):
		StringField.__init__(self, parent, attrs)
		self.sizeName = '%s.size' % self.name

	def set(self, record, value, test_state=True, modified=False):
		record.values[self.name] = None
		record.values[self.sizeName] = False
		if value:
			if record.isWizard():
				value = base64.decodestring(value)
				record.values[self.name] = value
				if value:
					record.values[ self.sizeName ] = Numeric.bytesToText( len(value) )
				else:
					record.values[ self.sizeName ] = ''
			else:
				record.values[ self.sizeName ] = value
		if modified:
			record.modified = True
			record.modified_fields.setdefault(self.name)

	def set_client(self, record, value, test_state=True):
		internal = record.values.get(self.name, None)
		record.values[self.name] = value
		if value:
			record.values[self.sizeName] = Numeric.bytesToText( len(value or '') )
		else:
			record.values[self.sizeName] = ''
		if internal != record.values[self.name]:
			self.changed(record)

	def get(self, record, checkLoad=True, readonly=True, modified=False):
		if checkLoad:
			# Only load from the server if checkLoad is True
			value = self.get_client(record)
		else:
			value = record.values[self.name]
		if value:
			value = base64.encodestring(value)
		else:
			# OpenERP 5.0 server doesn't like False as a value for Binary fields.
			value = ''
		return value

	def get_client(self, record):
		if record.values[self.name] is None and record.id:
			c = Rpc.session.context.copy()
			c.update(record.context())
			value = record.rpc.read([record.id], [self.name], c)[0][self.name]
			if value:
				record.values[self.name] = base64.decodestring(value)
			else:
				record.values[self.name] = ''
		return record.values[self.name]

class BinarySizeField(StringField):
	def __init__(self, parent, attrs):
		StringField.__init__(self, parent, attrs)
		self.name = '%s.size' % attrs['name']

	def set(self, record, value, test_state=True, modified=False):
		record.values[self.name] = value
		# Do not mark as modified


class SelectionField(StringField):
	def set(self, record, value, test_state=True, modified=False):
		if value in [sel[0] for sel in self.attrs['selection']]:
			super(SelectionField, self).set(record, value, test_state, modified)

class FloatField(StringField):
	def validate(self, record):
		record.setFieldValid( self.name, True )
		return True

	def set_client(self, record, value, test_state=True):
		internal = record.values[self.name]
		self.set(record, value, test_state)
		digits = self.attrs.get('digits', (14,2))
		# Use floatToText as the comparison we inherited from the GTK client failed for us in some cases
		# were python was considering the difference between 145,13 and 145,12 as 0,009999999 instead of 0,01
		# Converting to string the numbers with the appropiate number of digits make it much easier.
		if Numeric.floatToText( internal, digits ) != Numeric.floatToText( record.values[self.name], digits ):
			if not record.isFieldReadOnly( self.name ):
				self.changed(record)

class IntegerField(StringField):

	def get(self, record, checkLoad=True, readonly=True, modified=False):
		return record.values.get(self.name, 0) or 0

	def get_client(self, record):
		return record.values[self.name] or 0

	def validate(self, record):
		record.setFieldValid( self.name, True )
		return True


class ManyToOneField(StringField):
		
	def get(self, record, checkLoad=True, readonly=True, modified=False):
		if record.values[self.name]:
			return record.values[self.name][0] or False
		return False

	def get_client(self, record):
		if record.values[self.name]:
			return record.values[self.name][1]
		return False

	def set(self, record, value, test_state=False, modified=False):
		if value and isinstance(value, (int, str, unicode, long)):
			Rpc2 = RpcProxy(self.attrs['relation'])
			result = Rpc2.name_get([value], Rpc.session.context)

			# In some very rare cases we may get an empty
			# list from the server so we just check it before
			# trying to store result[0]
			if result:
				record.values[self.name] = result[0]
		else:
			record.values[self.name] = value
		if modified:
			record.modified = True
			record.modified_fields.setdefault(self.name)

	def set_client(self, record, value, test_state=False):
		internal = record.values[self.name]
		self.set(record, value, test_state)
		if internal != record.values[self.name]:
			self.changed(record)

# This is the base class for ManyToManyField and OneToManyField
# The only difference between these classes is the 'get()' method.
# In the case of ManyToMany we always return all elements because
# it only stores the relation between two records which already exist.
# In the case of OneToMany we only return those objects that have 
# been modified because the pointed object stores the relation to the
# parent.
class ToManyField(StringField):
	def create(self, record):
		from Koo.Model.Group import RecordGroup
		group = RecordGroup(resource=self.attrs['relation'], fields={}, parent=record, context=self.context(record, eval=False))
		group.setDomainForEmptyGroup()
		group.tomanyfield = self
		self.connect( group, SIGNAL('modified'), self.groupModified )
		return group

	def groupModified(self):
		p = self.sender().parent
		self.changed( self.sender().parent )

	def get_client(self, record):
		return record.values[self.name]

	def get(self, record, checkLoad=True, readonly=True, modified=False):
		pass

	def set(self, record, value, test_state=False, modified=False):
		from Koo.Model.Group import RecordGroup
		# We can't add the context here as it might cause an infinite loop in some cases where
		# a field of the parent appears in the context, and the parent is just being loaded.
		# This has crashed when switching view of the 'account.invoice.line' one2many field
		# in 'account.invoice' view.
		group = RecordGroup(resource=self.attrs['relation'], fields={}, parent=record, context=self.context(record, eval=False))
		group.tomanyfield = self
		self.connect( group, SIGNAL('modified'), self.groupModified )
		group.setDomain( [('id','in',value)] )
		group.load(value)
		record.values[self.name] = group
		if modified:
			self.changed(record)

	def set_client(self, record, value, test_state=False):
		self.set(record, value, test_state=test_state)
		self.changed(record)

	def validate(self, record):
		ok = True
		for record in record.values[self.name].modifiedRecords():
			if not record.validate():
				ok = False
		if not super(ToManyField, self).validate(record):
			ok = False
		record.setFieldValid( self.name, ok )
		return ok

class OneToManyField(ToManyField):
	def get(self, record, checkLoad=True, readonly=True, modified=False):
		if not record.values[self.name]:
			return []
		result = []
		group = record.values[self.name]
		# Update modified records
		for modifiedRecord in group.modifiedRecords():
			# New records are also returned by the modifiedRecords() function
			if modifiedRecord.id:
				result.append((1, modifiedRecord.id, modifiedRecord.get(checkLoad=checkLoad, get_readonly=readonly)))

		# Add new records
		for rec in group.newRecords():
			result.append((0, 0, rec.get(checkLoad=checkLoad, get_readonly=readonly)))

		# Remove removed records
		for id in record.values[self.name].removedRecords:
			result.append( (2, id, False) )
		return result

	def setDefault(self, record, value):
		from Koo.Model.Group import RecordGroup
		fields = {}
		if value and len(value):
			context = self.context(record)
			Rpc2 = RpcProxy(self.attrs['relation'])
			fields = Rpc2.fields_get(value[0].keys(), context)

		record.values[self.name] = RecordGroup(resource=self.attrs['relation'], fields=fields, parent=record, context=self.context(record, eval=False))
		self.connect( record.values[self.name], SIGNAL('modified'), self.groupModified )
		record.values[self.name].tomanyfield = self
		mod=None
		for record in (value or []):
			# TODO: Fix with new Group behaviour. Has this ever really worked?
			mod = record.values[self.name].model_new(default=False)
			mod.setDefault(record)
			record.values[self.name].model_add(mod)
		return True

	def default(self, record):
		# TODO: Fix with new Group behaviour. Has this ever really worked?
		return [ x.defaults() for x in record.values[self.name].records ]

class ManyToManyField(ToManyField):
	def get(self, record, checkLoad=True, readonly=True, modified=False):
		if not record.values[self.name]:
			return []
		return [(6, 0, record.values[self.name].ids())]

	def default(self, record):
		if not record.values[self.name]:
			return []
		return record.values[self.name].ids()

class ReferenceField(StringField):
	def get_client(self, record):
		if record.values[self.name]:
			return record.values[self.name]
		return False

	def get(self, record, checkLoad=True, readonly=True, modified=False):
		if record.values[self.name]:
			return '%s,%d' % (record.values[self.name][0], record.values[self.name][1][0])
		return False

	def set_client(self, record, value):
		internal = record.values[self.name]
		record.values[self.name] = value
		if (internal or False) != (record.values[self.name] or False):
			self.changed(record)

	def set(self, record, value, test_state=False, modified=False):
		if not value:
			record.values[self.name] = False
			return
		ref_model, id = value.split(',')
		# id must be an integer
		id = int(id)
		Rpc2 = RpcProxy(ref_model)
		result = Rpc2.name_get([id], Rpc.session.context)
		if result:
			record.values[self.name] = ref_model, result[0]
		else:
			record.values[self.name] = False
		if modified:
			record.modified = True
			record.modified_fields.setdefault(self.name)


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
		'binary-size': BinarySizeField,
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
