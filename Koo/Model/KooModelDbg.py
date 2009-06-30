##############################################################################
#
# Copyright (c) 2009 P. Christeas <p_christ@hol.gr>
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

from KooModel import *

## @ Brief Debugging version of KooModel, prints notifications
class KooModelDbg(KooModel):
	
	def __call__(self, method, *params):
		print "Calling KooModel.%s"%(str(method))
		return KooModel.__call__(self,method, *params)

	def id(self, index):
		print "id"
		return KooModel.id(self,index)
	
	def rowCount(self, parent = QModelIndex()):
		print "Rowcount for",parent
		return KooModel.rowCount(self,parent)
		
	def data(self, index, role=Qt.DisplayRole ):
		print "date for ",index
		return KooModel.data(self,index,role)