##############################################################################
#
# Copyright (c) 2008 Albert Cervera i Areny <albert@nan-tic.com>
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

import copy

class AbstractCache:
	def exists( self, obj, method, *args ):
		pass
	def get( self, obj, method, *args ):
		pass

class ViewCache(AbstractCache):
	exceptions = []

	def __init__(self):
		self.cache = {}

	def exists(self, obj, method, *args):
		if method != 'execute' or len(args) < 2 or args[1] != 'fields_view_get':
			return False
		return (obj, method, str(args)) in self.cache
			
	def get(self, obj, method, *args):
		return copy.deepcopy( self.cache[(obj, method, str(args))] )

	def add(self, value, obj, method, *args):
		if method != 'execute' or len(args) < 2 or args[1] != 'fields_view_get':
			return
		# Don't cache models configured in the exception list of the server module 'koo'.
		if args[0] in ViewCache.exceptions:
			return False
		self.cache[(obj,method,str(args))] = copy.deepcopy( value )

	def clear(self):
		self.cache = {}

class ActionViewCache(AbstractCache):
	exceptions = []

	def __init__(self):
		self.cache = {}

	def exists(self, obj, method, *args):
		if method == 'execute' and len(args) >= 3 and args[1] == 'search' and ( args[2] == [('id','in',[])] or args[2] == [['id','in',[]]] ):
			# In cases where search filter only is equal to [('id','in',[])] we will optimize and return
			# an empty list. This is a usual call produced by empty many2many or one2many relations so it's
			# worth the taking it into account.
			return True
		if method == 'execute' and len(args) >= 2 and args[1] == 'fields_view_get':
			return (obj, method, str(args)) in self.cache
		elif method == 'execute' and len(args) >= 2 and args[0] == 'ir.values' and args[1] == 'get':
			return (obj, method, str(args)) in self.cache
		elif obj == '/fulltextsearch' and method == 'indexedModels':
			return (obj, method, str(args)) in self.cache
		else:
			return False
			
	def get(self, obj, method, *args):
		if method == 'execute' and len(args) >= 3 and args[1] == 'search' and ( args[2] == [('id','in',[])] or args[2] == [['id','in',[]]] ):
			# In cases where search filter only is equal to [('id','in',[])] we will optimize and return
			# an empty list. This is a usual call produced by empty many2many or one2many relations so it's
			# worth the taking it into account.
			return []
		return copy.deepcopy( self.cache[(obj, method, str(args))] )
		
	def add(self, value, obj, method, *args):
		# No need to consider 'search' with [('id','in',[])] here given that we don't have to store anything
		if method == 'execute' and len(args) >= 2 and args[1] == 'fields_view_get':
			# Don't cache models configured in the exception list of the server module 'koo'.
			if args[0] in ViewCache.exceptions:
				return 
			self.cache[(obj,method,str(args))] = copy.deepcopy( value )
		elif method == 'execute' and len(args) >= 2 and args[0] == 'ir.values' and args[1] == 'get':
			self.cache[(obj,method,str(args))] = copy.deepcopy( value )
		elif obj == '/fulltextsearch' and method == 'indexedModels':
			self.cache[(obj,method,str(args))] = copy.deepcopy( value )

	def clear(self):
		self.cache = {}

