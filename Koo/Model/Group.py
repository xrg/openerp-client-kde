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

from Koo.Rpc import RpcProxy
from Koo import Rpc
from Koo.Common.Settings import *
from Record import Record
import Field 


from PyQt4.QtCore import *
from PyQt4.QtGui import *

try:
	set()
except NameError:
	from sets import Set as set

## @brief The RecordGroup class manages a list of records.
# 
# Provides functions for loading, storing and creating new objects of the same type.
# The 'fields' property stores a dictionary of dictionaries, each of which contains 
# information about a field. This information includes the data type ('type'), its name
# ('name') and other attributes. The 'fieldObjects' property stores the classes responsible
# for managing the values which are finally stored on the 'values' dictionary in the
# Model
#
# The group can also be sorted by any of it's fields. Two sorting methods are provided:
# SortVisibleItems and SortAllItems. SortVisibleItems is usually faster for a small
# number of elements as sorting is handled on the client side, but only those loaded
# are considered in the sorting. SortAllItems, sorts items in the server so all items
# are considered. Although this would cost a lot when there are thousands of items, 
# only some of them are loaded and the rest are loaded on demand.
#
# Note that by default the group will handle (and eventually load) all records that match 
# the conditions imposed by 'domain' and 'filter'. Those are empty by default so creating 
# RecordGroup('res.parnter') and iterating through it's items will return all partners
# in the database. If you want to ensure that the group is kept completely empty, you can
# call setAllowRecordLoading( False ) which is equivalent to calling setFilter() with a filter 
# that no records match, but without the overhead of querying the server.
#
# RecordGroup will emit several kinds of signals on certain events. 
class RecordGroup(QObject):

	SortVisibleItems = 1
	SortAllItems = 2

	SortingPossible = 0
	SortingNotPossible = 1
	SortingOnlyGroups = 2
	SortingNotPossibleModified = 3

	## @brief Creates a new RecordGroup object.
	# @param resource Name of the model to load. Such as 'res.partner'.
	# @param fields Dictionary with the fields to load. This value typically comes from the server.
	# @param ids Record identifiers to load in the group.
	# @param parent Only used if this RecordGroup serves as a relation to another model. Otherwise it's None.
	# @param context Context for RPC calls.
	def __init__(self, resource, fields = None, ids=None, parent=None, context=None):
		QObject.__init__(self)
		if ids is None:
			ids = []
		if context is None:
			context = {}
		self.parent = parent
		self._context = context
		self._context.update(Rpc.session.context)
		self.resource = resource
		self.limit = Settings.value( 'koo.limit', 80, int )
		self.maximumLimit = self.limit
		self.rpc = RpcProxy(resource)
		if fields == None:
			self.fields = {}
		else:
			self.fields = fields
		self.fieldObjects = {}
		self.loadFieldObjects( self.fields.keys() )

		self.records = []

		self.enableSignals()
		
		# toBeSorted properties store information each time sort() function
		# is called. If loading of records is not enabled, records won't be
		# loaded but we keep by which field we want information to be sorted
		# so when record loading is enabled again we know how should the sorting
		# be.
		self.toBeSortedField = None
		self.toBeSortedOrder = None

		self.sortedField = None
		self.sortedOrder = None
		self.updated = False
		self._domain = []
		self._filter = []

		if Settings.value('koo.sort_mode') == 'visible_items':
			self._sortMode = self.SortVisibleItems
		else:
			self._sortMode = self.SortAllItems
		self._sortMode = self.SortAllItems

		self.load(ids)
		self.removedRecords = []
		self._onWriteFunction = ''

	## @brief Sets wether data loading should be done on record chunks or one by one.
	#
	# Setting value to True, will make the RecordGroup ignore the current 'limit' property,
	# and load records by one by, instead. If set to False (the default) it will load records
	# in groups of 'limit' (80, by default).
	#
	# In some cases (widgets that show multiple records) it's better to load in chunks, in other
	# cases, it's better to load one by one.
	def setLoadOneByOne(self, value):
		if value:
			self.limit = 1
		else:
			self.limit = self.maximumLimit

	def setSortMode(self, mode):
		self._sortMode = mode

	def sortMode(self):
		return self._sortMode

	def setOnWriteFunction(self, value):
		self._onWriteFunction = value

	def onWriteFunction(self):
		return self._onWriteFunction

	def __del__(self):
		self.rpc = None
		self.parent = None
		self.resource = None
		self._context = None
		self.fields = None
		for r in self.records:
			if not isinstance(r, Record):
				continue
			r.__del__()
		self.records = []
		for f in self.fieldObjects:
			self.fieldObjects[f].parent = None
			self.fieldObjects[f].setParent( None )
			#self.disconnect( self.fieldObjects[f], None, 0, 0 )
			#self.fieldObjects[f] = None
			#del self.fieldObjects[f]
		self.fieldObjects = {}

	## @brief Returns a string with the name of the type of a given field. Such as 'char'.
	def fieldType( self, fieldName ):
		if not fieldName in self.fields:
			return None
		return self.fields[fieldName]['type']

	# Creates the entries in 'fieldObjects' for each key of the 'fkeys' list.
	def loadFieldObjects(self, fkeys):
		for fname in fkeys:
			fvalue = self.fields[fname]
			fvalue['name'] = fname
			self.fieldObjects[fname] = Field.FieldFactory.create( fvalue['type'], self, fvalue )
			if fvalue['type'] in ('binary','image'):
				self.fieldObjects['%s.size' % fname] = Field.FieldFactory.create( 'binary-size', self, fvalue )

	## @brief Saves all the records. 
	#
	# Note that there will be one request to the server per modified or 
	# created record.
	def save(self):
		for record in self.records:
			if isinstance( record, Record ):
				saved = record.save()

	## @brief Returns a list with all modified records
	def modifiedRecords(self):
		modified = []
		for record in self.records:
			if isinstance( record, Record ) and record.isModified():
				modified.append( record )
		return modified

	## @brief This function executes the 'onWriteFunction' function in the server.
	#
	# If there is a 'onWriteFunction' function associated with the model type handled by 
	# this record group it will be executed. 'editedId' should provide the 
	# id of the just saved record.
	#
	# This functionality is provided here instead of on the record because
	# the remote function might update some other records, and they need to
	# be (re)loaded.
	def written( self, editedId ):
		if not self._onWriteFunction or not editedId:
			return
		# Execute the onWriteFunction function on the server.
		# It's expected it'll return a list of ids to be loaded or reloaded.
		new_ids = getattr(self.rpc, self._onWriteFunction)( editedId, self.context() )
		record_idx = self.records.index( self.recordById( editedId ) )
		result = False
		indexes = []
		for id in new_ids:
			cont = False
			for m in self.records:
				if isinstance( m, Record ):
					if m.id == id:
						cont = True
						# TODO: Shouldn't we just call cancel() so the record
						# is reloaded on demand?
						m.reload()
			if cont:
				continue
			# TODO: Should we reconsider this? Do we need/want to reload. Probably we
			# only want to add the id to the list.
			record = Record(id, self, parent=self.parent)
			self.connect(record,SIGNAL('recordChanged( PyQt_PyObject )'), self.recordChanged )
			self.connect(record,SIGNAL('recordModified( PyQt_PyObject )'),self.recordModified)
			record.reload()
			if not result:
				result = record
			newIndex = min(record_idx, len(self.records)-1)
			self.add(record, newIndex)
			indexes.append(newIndex)

		if indexes:
			self.emit( SIGNAL('recordsInserted(int,int)'), min(indexes), max(indexes) )
		return result
	
	## @brief Adds a list of records as specified by 'values'.
	#
	# 'values' has to be a list of dictionaries, each of which containing fields
	# names -> values. At least key 'id' needs to be in all dictionaries.
	def loadFromValues(self, values):
		start = len(self.records)
		for value in values:
			record = Record(value['id'], self, parent=self.parent)
			record.set(value)
			self.records.append(record)
			self.connect(record,SIGNAL('recordChanged( PyQt_PyObject )'), self.recordChanged )
			self.connect(record,SIGNAL('recordModified( PyQt_PyObject )'),self.recordModified)
		end = len(self.records)-1
		self.emit( SIGNAL('recordsInserted(int,int)'), start, end )
	
	## @brief Creates as many records as len(ids) with the ids[x] as id.
	#
	# 'ids' needs to be a list of identifiers. The addFields() function
	# can be used later to load the necessary fields for each record.
	def load(self, ids, addOnTop=False):
		if not ids:
			return 
		if addOnTop:
			start = 0
			# Discard from 'ids' those that are already loaded.
			# If we didn't do that, some records could be repeated if the programmer
			# doesn't verify that, and we'd end up in errors because when records are
			# actually loaded they're only checked against a single appearance of the 
			# id in the list of records.
			#
			# Note we don't use sets to discard ids, because we want to keep the order
			# their order and because it can cause infinite recursion.
			currentIds = self.ids()
			for id in ids:
				if id not in currentIds:
					self.records.insert( 0, id )
			end = len(ids)-1
		else:
			start = len(self.records)
			# Discard from 'ids' those that are already loaded. Same as above.
			currentIds = self.ids()
			for id in ids:
				if id not in currentIds:
					self.records.append( id )
			end = len(self.records)-1
		# We consider the group is updated because otherwise calling count() would
		# force an update() which would cause one2many relations to load elements
		# when we only want to know how many are there.
		self.updated = True
		self.emit( SIGNAL('recordsInserted(int,int)'), start, end )

	## @brief Clears the list of records. It doesn't remove them.
	def clear(self):
		for record in self.records:
			if isinstance(record, Record):
				self.disconnect( record, SIGNAL('recordChanged( PyQt_PyObject )'), self.recordChanged )
				self.disconnect( record, SIGNAL('recordModified( PyQt_PyObject )'), self.recordModified )
		last = len(self.records)-1
		self.records = []
		self.removedRecords = []
		self.emit( SIGNAL('recordsRemoved(int,int)'), 0, last )
	
	## @brief Returns a copy of the current context
	def context(self):
		ctx = {}
		ctx.update(self._context)
		return ctx

	## @brief Sets the context that will be used for RPC calls.
	def setContext(self, context):
		self._context = context.copy()

	## @brief Adds a record to the list
	def add(self, record, position=-1):
		if not record.group is self:
			fields = {}
			for mf in record.group.fields:
				fields[record.group.fields[mf]['name']] = record.group.fields[mf]
			self.addFields(fields)
			record.group.addFields(self.fields)
			record.group = self

		if position==-1:
			self.records.append(record)
		else:
			self.records.insert(position, record)
		record.parent = self.parent
		self.connect(record,SIGNAL('recordChanged( PyQt_PyObject )'),self.recordChanged)
		self.connect(record,SIGNAL('recordModified( PyQt_PyObject )'),self.recordModified)
		return record

	## @brief Creates a new record of the same type of the records in the group.
	#
	# If 'default' is true, the record is filled in with default values. 
	# 'domain' and 'context' are only used if default is true.
	def create(self, default=True, position=-1, domain=None, context=None):
		if domain is None:
			domain = []
		if context is None:
			context = {}
		self.ensureUpdated()

		record = Record(None, self, parent=self.parent, new=True)
		if default:
			ctx=context.copy()
			ctx.update( self.context() )
			record.fillWithDefaults(domain, ctx)
		self.add( record, position )
		if position == -1:
			start = len(self.records) - 1
		else:
			start = position
		self.emit( SIGNAL('recordsInserted(int,int)'), start, start )
		return record

	def disableSignals(self):
		self._signalsEnabled = False

	def enableSignals(self):
		self._signalsEnabled = True
	
	def recordChanged(self, record):
		if self._signalsEnabled:
			self.emit( SIGNAL('recordChanged(PyQt_PyObject)'), record )

	def recordModified(self, record):
		if self._signalsEnabled:
			self.emit( SIGNAL('modified') )

	## @brief Removes a record from the record group but not from the server.
	#
	# If the record doesn't exist it will ignore it silently.
	def removeRecord(self, record):
		idx = self.records.index(record)
		if isinstance( record, Record ):
			id = record.id
		else:
			id = record
		if id:
			# Only store removedRecords if they have a valid Id.
			# Otherwise we don't need them because they don't have 
			# to be removed in the server.
			self.removedRecords.append( id )
		if isinstance( record, Record ):
			if record.parent:
				record.parent.modified = True
		self.freeRecord( record )
		self.emit( SIGNAL('modified') )
		self.emit( SIGNAL('recordsRemoved(int,int)'), idx, idx )

	## @brief Remove a list of records from the record group but not from the server.
	#
	# If a record doesn't exist it will ignore it silently.
	def removeRecords(self, records):
		firstIdx = -1
		lastIdx = -1
		toRemove = []
		for record in records:
			if not record in records:
				continue
			idx = self.records.index(record)
			if firstIdx < 0 or idx < firstIdx:
				firstIdx = idx
			if lastIdx < 0 or idx > lastIdx:
				lastIdx = idx
			if isinstance( record, Record ):
				id = record.id
			else:
				id = record
			if id:
				# Only store removedRecords if they have a valid Id.
				# Otherwise we don't need them because they don't have 
				# to be removed in the server.
				self.removedRecords.append( id )
			if isinstance( record, Record ):
				if record.parent:
					record.parent.modified = True
			self.freeRecord( record )
		self.emit( SIGNAL('modified') )
		self.emit( SIGNAL('recordsRemoved(int,int)'), firstIdx, lastIdx )

	## @brief Removes a record from the record group but not from the server.
	#
	# If the record doesn't exist it will ignore it silently.
	def remove(self, record):
		if isinstance(record, list):
			self.removeRecords( record )
		else:
			self.removeRecord( record )	

	def binaryFieldNames(self):
		return [x[:-5] for x in self.fieldObjects.keys() if x.endswith('.size')]

	def allFieldNames(self):
		return [x for x in self.fieldObjects.keys() if not x.endswith('.size')]

	## @brief Adds the specified fields to the record group
	#
	# Note that it updates 'fields' and 'fieldObjects' in the group.
	# 'fields' is a dict of dicts as typically returned by 
	# the server.
	def addFields(self, fields):
		to_add = []
		for f in fields.keys():
			if not f in self.fields:
				self.fields[f] = fields[f]
				self.fields[f]['name'] = f
				to_add.append(f)
			else:
				self.fields[f].update(fields[f])
		self.loadFieldObjects(to_add)
		return to_add


	## @brief Ensures all records in the group are loaded.
	def ensureAllLoaded(self):
		ids = self.unloadedIds()
		c = Rpc.session.context.copy()
		c.update( self.context() )
		c['bin_size'] = True
		values = self.rpc.read( ids, self.fields.keys(), c )
		if values:
			for v in values:
				#self.recordById( v['id'] ).set(v, signal=False)
				r = self.recordById( v['id'] )
				r.set(v, signal=False)

	## @brief Returns the list of ids that have not been loaded yet. The list
	# won't include new records as those have id 0 or None.
	def unloadedIds(self):
		self.ensureUpdated()
		ids = []
		for x in self.records:
			if isinstance(x, Record):
				if x.id and not x._loaded:
					ids.append( x.id )
			elif x:
				ids.append( x )
		return ids

	## @brief Returns the list of loaded records. The list won't include new records.
	def loadedRecords(self):
		records = []
		for x in self.records:
			if isinstance(x, Record):
				if x.id and x._loaded:
					records.append( x )
		return records

	## @brief Returns a list with all ids.
	def ids(self):
		ids = []
		for x in self.records:
			if isinstance(x, Record):
				ids.append( x.id )
			else:
				ids.append( x )
		return ids

	## @brief Returns a list with all new records.
	def newRecords(self):
		records = []
		for x in self.records:
			if not isinstance(x, Record):
				continue
			if x.id:
				continue
			records.append( x )
		return records

	## @brief Returns the number of records in this group.
	def count(self):
		self.ensureUpdated()
		return len(self.records)

	def __iter__(self):
		self.ensureUpdated()
		self.ensureAllLoaded()
		return iter(self.records)

	## @brief Returns the record with id 'id'. You can use [] instead.
	# Note that it will check if the record is loaded and load it if not.
	def modelById(self, id):
		record = self.recordById( id )
		if not record:
			return None
		return record
	__getitem__ = modelById

	## @brief Returns the record at the specified row number.
	def modelByIndex(self, row):
		record = self.recordByIndex( row )
		return record

	## @brief Returns the row number of the given record. Note that
	# the record must be in the group. Otherwise an exception is risen.
	def indexOfRecord(self, record):
		if record in self.records:
			return self.records.index(record)
		else:
			return -1
		
	## @brief Returns the row number of the given id.
	# If the id doesn't exist it returns -1.
	def indexOfId(self, id):
		i = 0
		for record in self.records:
			if isinstance( record, Record ):
				if record.id == id:
					return i
			elif record == id:
				return i
			i += 1
		return -1

	## @brief Returns True if the given record exists in the group.
	def recordExists(self, record):
		return record in self.records

	## @brief Returns the record with id 'id'. You can use [] instead.
	# Note that it will return the record but won't try to load it.
	def recordById(self, id):
		for record in self.records:
			if isinstance( record, Record ):
				if record.id == id:
					return record
			elif record == id:
				idx = self.records.index( id )
				record = Record(id, self, parent=self.parent)
				self.connect(record,SIGNAL('recordChanged( PyQt_PyObject )'), self.recordChanged )
				self.connect(record,SIGNAL('recordModified( PyQt_PyObject )'),self.recordModified)
				self.records[idx] = record 
				return record

	## @brief Returns a Record object for the given row.
	def recordByIndex(self, row):
		if row < len(self.records):
			record = self.records[row]
		else:
			record = None
		if record and isinstance( record, Record ):
			return record
		else:
			record = Record(record, self, parent=self.parent)
			self.connect(record,SIGNAL('recordChanged( PyQt_PyObject )'), self.recordChanged )
			self.connect(record,SIGNAL('recordModified( PyQt_PyObject )'),self.recordModified)
			self.records[row] = record
			return record
	
	## @brief Returns True if the RecordGroup handles information of a wizard.
	def isWizard(self):
		return self.resource.startswith('wizard.')

	## @brief Checks whether the specified record is fully loaded and loads
	# it if necessary.
	def ensureModelLoaded(self, record):
		self.ensureUpdated()
		# Do not try to load if record is new.
		if not record.id:
			record.createMissingFields()
			return
		if record.isFullyLoaded():
			return

		c = Rpc.session.context.copy()
		c.update( self.context() )
		ids = self.ids()
		pos = ids.index(record.id) / self.limit

		queryIds = ids[pos * self.limit: pos * self.limit + self.limit]
		if None in queryIds:
			queryIds.remove( None )

		missingFields = record.missingFields()

		self.disableSignals()
		c['bin_size'] = True
		values = self.rpc.read(queryIds, missingFields, c)
		if values:
			for v in values:
				id = v['id']
				if 'id' not in missingFields:
					del v['id']
				self.recordById(id).set(v, signal=False)
		self.enableSignals()
		# TODO: Take a look if we need to set default values for new records!
		## Set defaults
		#if len(new) and len(to_add):
			#values = self.rpc.default_get( to_add, self.context() )
			#for t in to_add:
				#if t not in values:
					#values[t] = False
			#for mod in new:
				#mod.setDefaults(values)

	## @brief Allows setting the domain for this group of records.
	def setDomain(self, value):
		# In some (rare) cases we receive {} as domain. So let's just test
		# 'not value', and that should work in all cases, not only when value
		# is None.
		if not value:
			self._domain = []
		else:
			self._domain = value
		self.updated = False
	
	## @brief Returns the current domain.
	def domain(self):
		return self._domain

	## @brief Allows setting a filter for this group of records.
	#
	# The filter is conatenated to the domain to further restrict the records of
	# the group.
	def setFilter(self, value):
		if value == None:
			self._filter = []
		else:
			self._filter = value
		self.updated = False
	
	## @brief Returns the current filter.
	def filter(self):
		return self._filter

	## @brief Disables record loading by setting domain to [('id','in',[])]
	#
	# RecordGroup will optimize the case when domain + filter = [('id','in',[])]
	# by not even querying the server and searching ids. It will simply consider
	# the result is [] and thus the group will be kept empty.
	#
	# Domain may be changed using setDomain() function.
	def setDomainForEmptyGroup(self):
		self.setDomain([('id','in',[])])
		self.clear()

	## @brief Returns True if domain is [('id','in',[])]
	def isDomainForEmptyGroup(self):
		return self.domain() == [('id','in',[])]

	## @brief Reload the record group with current selected sort field, order, domain and filter
	def update(self):
		# Update context from Rpc.session.context as language
		# (or other settings) might have changed.
		self._context.update(Rpc.session.context)
		self.rpc = RpcProxy(self.resource)
		## Make it reload again
		self.updated = False
		self.sort( self.toBeSortedField, self.toBeSortedOrder )

	## @brief Ensures the group is updated.
	def ensureUpdated(self):
		if self.updated:
			return
		self.update()

	## @brief Sorts the group by the given field name.
	def sort(self, field, order):
		self.toBeSortedField = field
		self.toBeSortedOrder = order
		if self._sortMode == self.SortAllItems:
			self.sortAll( field, order )
		else:
			self.sortVisible( field, order )

	# Sorts the records in the group using ALL records in the database
	def sortAll(self, field, order):
		if self.updated and field == self.sortedField and order == self.sortedOrder:
			return

		# Check there're no new or modified fields. If there are
		# we won't sort as it means reloading data from the server
		# and we'd loose current changes.
		if self.isModified():
			self.emit( SIGNAL("sorting"), self.SortingNotPossibleModified )
			return

		oldSortedField = self.sortedField

		# We set this fields in the very beggining in case some signals are cought
		# and retry to sort again which would cause an infinite recursion.
		self.sortedField = field
		self.sortedOrder = order
		self.updated = True

		sorted = False
		sortingResult = self.SortingPossible

		if self._domain + self._filter == [('id','in',[])]:
			# If setDomainForEmptyGroup() was called, or simply the domain
			# included no tuples, we don't even need to query the server.
			# Note that this may be quite important in some wizards because
			# the model will actually not exist in the server and would raise
			# an exception.
			ids = []
		elif not field in self.fields.keys():
			# If the field doesn't exist use default sorting. Usually this will
			# happen when we update and haven't selected a field to sort by.
			ids = self.rpc.search( self._domain + self._filter, 0, False, False, self._context )
		else:
			type = self.fields[field]['type']
			if type == 'one2many' or type == 'many2many':
				# We're not able to sort 2many fields
				sortingResult = self.SortingNotPossible
			elif type == 'many2one':
				#orderby = '"%s"' % field 
				orderby = '%s' % field
				if order == Qt.AscendingOrder:
					orderby += " ASC"
				else:
					orderby += " DESC"
				try:
					ids = Rpc.session.call('/koo', 'search', self.resource, self._domain + self._filter, 0, 0, orderby, self._context )
					sortingResult = self.SortingPossible
					sorted = True
				except:
					sortingResult = self.SortingOnlyGroups

			# We check whether the field is stored or not. In case the server 
			# is not _ready_ we consider it's stored and we'll catch the exception
			# later.
			stored = self.fields[field].get('stored',True)
			if not stored:
				sortingResult = self.SortingNotPossible

			if not sorted and sortingResult != self.SortingNotPossible:
				# A lot of the work done here should be done on the server by core OpenERP
				# functions. This means this runs slower than it should due to network and
				# serialization latency. Even more, we lack some information to make it 
				# work well.

				# Ensure the field is quoted, otherwise fields such as 'to' can't be sorted
				# and return an exception.
				#orderby = '"%s"' % field 
				orderby = '%s' % field
				if order == Qt.AscendingOrder:
					orderby += " ASC"
				else:
					orderby += " DESC"

				try:
					# Use call to catch exceptions
					ids = Rpc.session.call('/object', 'execute', self.resource, 'search', self._domain + self._filter, 0, 0, orderby, self._context )
				except:
					# In functional fields not stored in the database this will
					# cause an exception :(
					sortingResult = self.SortingNotPossible

		if sortingResult != self.SortingNotPossible:
			self.clear()
			# The load function will be in charge of loading and sorting elements
			self.load( ids )
		elif oldSortedField == self.sortedField or not self.ids():
			# If last sorted field was the same as the current one, possibly only filter crierias have changed
			# so we might need to reload in this case. 
			# If sorting is not possible, but no data was loaded yet, we load by model default field and order.
			# Otherwise, a view might not load any data.
			ids = self.rpc.search(self._domain + self._filter, 0, 0, False, self._context )
			self.clear()
			# The load function will be in charge of loading and sorting elements
			self.load( ids )

		self.emit( SIGNAL("sorting"), sortingResult )

	# Sorts the records of the group taking into account only loaded fields.
	def sortVisible(self, field, order):
		if self.updated and field == self.sortedField and order == self.sortedOrder:
			return

		if not self.updated:
			ids = self.rpc.search( self._domain + self._filter, 0, self.limit, False, self._context )
			self.clear()
			self.load( ids )
		
		if not field in self.fields:
			return

		self.ensureAllLoaded()

		if field != self.sortedField:
			# Sort only if last sorted field was different than current

			# We need this function here as we use the 'field' variable
			def ignoreCase(record):
				v = record.value(field)
				if isinstance(v, unicode) or isinstance(v, str):
					return v.lower()
				else:
					return v

			type = self.fields[field]['type']
			if type == 'one2many' or type == 'many2many':
				self.records.sort( key=lambda x: len(x.value(field).group) )
			else:
				self.records.sort( key=ignoreCase )
			if order == Qt.DescendingOrder:
				self.records.reverse()
		else:
			# If we're only reversing the order, then reverse simply reverse
			if order != self.sortedOrder:
				self.records.reverse()

		self.sortedField = field
		self.sortedOrder = order
		self.updated = True

		# Emit recordsInserted() to ensure KooModel is updated.
		self.emit( SIGNAL('recordsInserted(int,int)'), 0, len(self.records)-1 )

		self.emit( SIGNAL("sorting"), self.SortingPossible )
		
	## @brief Removes all new records and marks all modified ones as not loaded.
	def cancel(self):
		for record in self.records[:]:
			if isinstance( record, Record ):
				if not record.id:
					self.freeRecord( record )
				elif record.isModified():
					record.cancel()
			else:
				if not record:
					self.freeRecord( record )

	## @brief Removes a record from the list (but not the record from the database).
	#
	# This function is used to take care signals are disconnected.
	def freeRecord(self, record):
		self.records.remove( record )
		if isinstance(record, Record):
			self.disconnect( record, SIGNAL('recordChanged( PyQt_PyObject )'), self.recordChanged )
			self.disconnect( record, SIGNAL('recordModified( PyQt_PyObject )'), self.recordModified )

	## @brief Returns True if any of the records in the group has been modified.
	def isModified(self):
		for record in self.records:
			if isinstance( record, Record ):
				if record.isModified():
					return True
		return False

	## @brief Returns True if the given record has been modified.
	def isRecordModified(self, id):
		for record in self.records:
			if isinstance( record, Record ):
				if record.id == id:
					return record.isModified()
			elif record == id:
				return False
		return False	

	## @brief Returns True if the given field is required in the RecordGroup, otherwise returns False.
	# Note that this is a flag for the whole group, but each record could have different values depending
	# on its state.
	def isFieldRequired(self, fieldName):
		required = self.fields[ fieldName ].get('required', False)
		if isinstance(required, bool):
			return required
		if isinstance(required, str) or isinstance(required, unicode):
			if required.lower() == 'true':
				return True
			if required.lower() == 'false':
				return False
		return bool(int(required))
		

# vim:noexpandtab:
