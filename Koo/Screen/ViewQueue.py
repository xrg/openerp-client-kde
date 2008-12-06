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

## @brief This class encapsulates the view types and ids handling for Screen.
#
# Model view definitions have an unintuitive way of handling which views should
# be shown. There are two ways of specifying it: view types and ids. The problem
# is that they can be combined. For example:
#   types = ['form','tree'] and ids = [24, False]
# What this class will do is convert those two lists into one more intuitive list:
#   views = [24, 'tree']
#
# You can initialize this class with values comming from a view definition using
# the setup function and then pickup each view. Example of usage:
# queue = ViewQueue()
# queue.setup( ['form','tree'], [24, False] )
# if queue.isType():
# 	useViewAsAType( queue.next() )

class ViewQueue:
	## @brief Initializes the queue with types and ids view definitions
	def setup(self, types, ids):
		if types == None:
			types = ['form', 'tree']
		if ids == None:
			ids = []
		# Merge lists
		self._views = []
		for x in range(max(len(types),len(ids))):
			if x < len(ids) and ids[x]:
				self._views.append( ids[x] )
			elif x < len(types):
				self._views.append( types[x] )

	## @brief Initializes the queue with a given list of view types.
	# If types is None then the list is initialized to the default ['form', 'tree']
	def setViewTypes(self, types):
		if types == None:
			self._views = ['form', 'tree']
		else:
			self._views = types

	## @brief Initializes the queue with a given list of view ids.
	def setViewIds(self, ids):
		self._views = ids

	## @brief Returns True if the next element is a view type.
	def isType(self):
		v = self._views[0]
		if isinstance(v,int):
			return False
		else:
			return True

	## @brief Returns True if the next element is a view id.
	def isId(self):
		return not self.isType()

	## @brief Returns True if the queue is empty.
	def isEmpty(self):
		return len(self._views) == 0

	## @brief Returns the next element of the queue.
	# 
	# If the queue is already empty, it will rise an exception.
	def next(self):
		return self._views.pop(0)

# vim:noexpandtab:
