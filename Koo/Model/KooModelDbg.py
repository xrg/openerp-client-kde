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

from PyQt4.QtCore import QModelIndex
import logging

def printMI(qmi, do_parent = True):
	if not isinstance(qmi, QModelIndex):
		return str(qmi)

	if not qmi.isValid():
		return "<null>"
	elif do_parent:
		return "(%d, %d)  @%s" % (qmi.row(), qmi.column(), printMI(qmi.parent()))
	else:
		return "(%d, %d)" % (qmi.row(), qmi.column())


## @ Brief Debugging version of KooModel, prints notifications
class KooModelDbg(KooModel):
	def __init__(self, *args,**kwargs):
		KooModel.__init__(self,*args,**kwargs)
		self.__logger = logging.getLogger('koo.model')
		
	def __call__(self, method, *params):
		self.__logger.debug("call km.%s"%(str(method)))
		return KooModel.__call__(self,method, *params)

	def id(self, index):
		self.__logger.debug("id: %s", printMI(index))
		return KooModel.id(self,index)
	
	def rowCount(self, parent = QModelIndex()):
		rc = KooModel.rowCount(self,parent)
		self.__logger.debug("Rowcount for %s: %d",printMI(parent), rc)
		return rc

	def columnCount(self, parent = QModelIndex()):
		rc = KooModel.columnCount(self,parent)
		self.__logger.debug("Columncount for %s: %d",printMI(parent), rc)
		return rc

	def data(self, index, role=Qt.DisplayRole ):
		da = None
		try:
			da = KooModel.data(self,index,role)
		finally:
			self.__logger.debug("data for %s{%s} = %s",printMI(index), role , str(da))
		return da