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
from Koo.Common import Options
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

	## @brief Creates a new RecordGroup object.
	# @param resource Name of the model to load. Such as 'res.partner'.
	# @param fields Dictionary with the fields to load. This value typically comes from the server.
	# @param ids Record identifiers to load in the group.
	# @param parent Only used if this RecordGroup serves as a relation to another model. Otherwise it's None.
	# @param context Context for RPC calls.
	def __init__(self, resource, fields = None, ids=[], parent=None, context={}):
		QObject.__init__(self)
		self.parent = parent
		self._context = context
		self._context.update(Rpc.session.context)
		self.resource = resource
		self.limit = Options.options.get( 'limit', 80 )
		self.rpc = RpcProxy(resource)
		if fields == None:
			self.fields = {}
		else:
			self.fields = fields
		self.fieldObjects = {}
		self.loadFieldObjects( self.fields.keys() )

		self.records = []
		
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
		self._allowRecordLoading = True

		if Options.options['sort_mode'] == 'visible_items':
			self._sortMode = self.SortVisibleItems
		else:
			self._sortMode = self.SortAllItems

		self.load(ids)
		self.removedRecords = []
		self._onWriteFunction = ''

	def setOnWriteFunction(self, value):
		self._onWriteFunction = value

	def onWriteFunction(self):
		return self._onWriteFunction

	def __del__(self):
		#print "DEL..."
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
		#print "F: ", self.fieldObjects
		for f in self.fieldObjects:
			self.fieldObjects[f].parent = None
			self.fieldObjects[f].setParent( None )
			#self.disconnect( self.fieldObjects[f], None, 0, 0 )
			#self.fieldObjects[f] = None
			#del self.fieldObjects[f]
		#print "DELETE"
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
			newmod = Record(id, self, parent=self.parent)
			self.connect(record,SIGNAL('recordChanged( PyQt_PyObject )'), self.recordChanged )
			self.connect(record,SIGNAL('recordModified( PyQt_PyObject )'),self.recordModified)
			newmod.reload()
			if not result:
				result = newmod
			newIndex = min(record_idx, len(self.records)-1)
			self.add(newmod, newIndex)
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
		self.emit( SIGNAL('recordsRemoved(int,int)'), 0, len(self.records)-1 )
		self.records = []
		self.removedRecords = []
	
	## @brief Returns a copy of the current context
	def context(self):
		ctx = {}
		ctx.update(self._context)
		return ctx

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
	def create(self, default=True, position=-1, domain=[], context={}):
		self.ensureUpdated()

		record = Record(None, self, parent=self.parent, new=True)
		self.connect(record,SIGNAL('recordChanged( PyQt_PyObject )'),self.recordChanged)
		self.connect(record,SIGNAL('recordModified( PyQt_PyObject )'),self.recordModified)
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
	
	def recordChanged(self, record):
		self.emit( SIGNAL('recordChanged(PyQt_PyObject)'), record )

	def recordModified(self, record):
		self.emit( SIGNAL('modified()') )

	## @brief Removes a record from the record group but not from the server.
	#
	# If the record doesn't exist it will ignore it silently.
	def remove(self, record):
		if not record in self.records:
			return
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
		self.emit( SIGNAL('modified()') )
		self.emit( SIGNAL('recordsRemoved(int,int)'), idx, idx )
		self.records.remove( record )

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
		values = self.rpc.read( ids, self.fields.keys(), c )
		if values:
			for v in values:
				#self.recordById( v['id'] ).set(v, signal=False)
				r = self.recordById( v['id'] )
				r.set(v, signal=False)

	## @brief Returns the list of ids that have not been loaded yet. The list
	# won't include new records as those have id 0 or None.
	def unloadedIds(self):
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
		self.ensureModelLoaded( record )
		return record
	__getitem__ = modelById

	## @brief Returns the record at the specified row number.
	def modelByIndex(self, row):
		record = self.recordByIndex( row )
		self.ensureModelLoaded(record)
		return record

	## @brief Returns the row number of the given record. Note that
	# the record must be in the group. Otherwise an exception is risen.
	def indexOfRecord(self, record):
		return self.records.index(record)
		
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
		record = self.records[row]
		if isinstance( record, Record ):
			return record
		else:
			record = Record(record, self, parent=self.parent)
			self.connect(record,SIGNAL('recordChanged( PyQt_PyObject )'), self.recordChanged )
			self.connect(record,SIGNAL('recordModified( PyQt_PyObject )'),self.recordModified)
			self.records[row] = record
			return record
		

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

		# Load only non binary and image fields
		binaries = [x for x in missingFields if self.fields[x]['type'] in ('binary','image')]
		others = list( set(missingFields) - set(binaries) )
		if others:
			values = self.rpc.read(queryIds, others, c)
			if values:
				for v in values:
					id = v['id']
					if 'id' not in others:
						del v['id']
					self.recordById(id).set(v, signal=False)
		if binaries:
			# We set binaries to the special value None so
			# the field will know it hasn't been loaded and thus
			# load data on demand when get() is called.
			data = {}
			for x in binaries:
				data[x] = None
			for x in queryIds:
				self.recordById(x).set( data )
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
		if value == None:
			self._domain = []
		else:
			self._domain = value
		self._allowRecordLoading  = True
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
		self._allowRecordLoading  = True
		self.updated = False
	
	## @brief Returns the current filter.
	def filter(self):
		return self._filter

	## @brief Enables or disables record loading. Sometimes it's desired that the record
	# won't load anything, as otherwise it would load records, by default.
	#
	# Calling setFilter() or setDomain() after this function will reallow record loading
	# if it's disallowed. If the following sequence happens:
	#
	# setAllowRecordLoading( False )
	# sort( 'name', Qt.Descending )
	# setAllowRecordLoading( True )
	# 
	# When setAllowRecordLoading( True ) is called, the record will be updated with the
	# latest sort parameters. That is, sorted by name in descending order.
	def setAllowRecordLoading(self, value):
		self._allowRecordLoading  = value
		if not value:
			self.clear()
		else:
			self.update()
	
	## @brief Returns whether record loading is enabled or not.
	def allowRecordLoading(self):
		return self._allowRecordLoading 

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
		if not self._allowRecordLoading:
			return
		if self.updated:
			return
		self.update()

	## @brief Sorts the group by the given field name.
	def sort(self, field, order):
		self.toBeSortedField = field
		self.toBeSortedOrder = order
		if not self._allowRecordLoading:
			return
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
			return

		sortingResult = self.SortingPossible

		if not field in self.fields.keys():
			# If the field doesn't exist use default sorting. Usually this will
			# happen when we update and haven't selected a field to sort by.
			ids = self.rpc.search( self._domain + self._filter, 0, False, False, self._context )
		else:
			type = self.fields[field]['type']
			if type == 'one2many' or type == 'many2many':
				# We're not able to sort 2many fields
				sortingResult = self.SortingNotPossible
			elif type == 'many2one':
				sortingResult = self.SortingOnlyGroups

			if sortingResult != self.SortingNotPossible:
				# A lot of the work done here should be done on the server by core OpenERP
				# functions. This means this runs slower than it should due to network and
				# serialization latency. Even more, we lack some information to make it 
				# work well.
				orderby = field + " "
				if order == Qt.AscendingOrder:
					orderby += "ASC"
				else:
					orderby += "DESC"
				try:
					# Use call to catch exceptions
					ids = Rpc.session.call('/object', 'execute', self.resource, 'search', self._domain + self._filter, 0, 0, orderby, self._context )
				except:
					# In functional fields not stored in the database this will
					# cause an exception :(
					sortingResult = self.SortingNotPossible
					#ids = self.rpc.search(self._domain + self._filter, 0, 0, False, self._context )

		if sortingResult == self.SortingNotPossible:
			# If sorting is not possible we ensure the "to be sorted" field
			# is not the one we're trying now.
			self.toBeSortedField = self.sortedField
			self.toBeSortedOrder = self.sortedOrder
		else:
			# We set this fields in the end in case some exceptions where fired 
			# in previous steps.
			self.sortedField = field
			self.sortedOrder = order
		self.updated = True

		self.clear()
		# The load function will be in charge of loading and sorting elements
		self.load( ids )

		# Send the signal at the very end because we don't want GUI applications to
		# retry loading which could cause an infinite recursion. We need to exit
		# this function with sortedField, toBeSortedField and updated flags properly
		# set.
		self.emit( SIGNAL("sorting"), sortingResult )

	# Sorts the records of the group taking into account only loaded fields.
	def sortVisible(self, field, order):
		if self.updated and field == self.sortedField and order == self.sortedOrder:
			return

		if not self.updated:
			ids = self.rpc( self._domain + self._filter, 0, self.limit, False, self._context )
			self.clear()
			self.load( ids )
		
		if not field in self.fields:
			return

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
		
	## @brief Removes all new records and marks all modified ones as not loaded.
	def cancel(self):
		for record in self.records[:]:
			if isinstance( record, Record ):
				if not record.id:
					self.records.remove( record )
				elif record.isModified():
					record.cancel()
			else:
				if not record:
					self.records.remove( record )

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
