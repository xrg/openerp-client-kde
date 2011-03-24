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

from AbstractFieldDelegate import *
from Koo.Common import Plugins
import os

## @brief The FieldDelegateFactory class specializes in creating the appropiate 
# delegates for a given type.

class FieldDelegateFactory:
	delegates = {}

	## @brief Scans for all available delegates.
	@staticmethod
	def scan():
		# Scan only once
		if FieldDelegateFactory.delegates:
			return
		# Search for all available views
		Plugins.scan( 'Koo.Fields', os.path.abspath(os.path.dirname(__file__)) )

	## @brief Creates a new delegate given type, parent and attributes.
	@staticmethod
	def create(delegateType, parent, attributes):
		FieldDelegateFactory.scan()
		if not delegateType in FieldDelegateFactory.delegates:
			return AbstractFieldDelegate( parent, attributes )

		# We do not support relational fields treated as selection ones
		if delegateType == 'selection' and 'relation' in attributes:
			delegateType = 'many2one'

		delegateClass = FieldDelegateFactory.delegates[delegateType]
		return delegateClass(parent, attributes)

	## @brief Registers a new delegate, given it's name (or type) and reference
	# to the class.
	@staticmethod
	def register( name, delegate ):
		FieldDelegateFactory.delegates[ name ] = delegate

