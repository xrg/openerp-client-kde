##############################################################################
#
# Copyright (c) 2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id: list.py 4411 2006-11-02 23:59:17Z pinky $
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

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from widget.view.abstractview import *

class ViewChart( AbstractView ) :
	def __init__(self, parent, toolbar=None ):
		AbstractView.__init__( self, parent )
		self.view_type = 'graph'
		self.model_add_new = False
		self.widget = None 
		layout = QVBoxLayout( )
		self.setLayout( layout )
		self.title= ''
		self.model = None

	def setWidget( self, widget ):
		self.widget = widget
		self.layout().addWidget( self.widget )

	def __getitem__(self, name):
		return None

 	def display(self, currentModel, models):
		# Maybe we could not load the charts, due to some missing modules
		# and thus we can't update it
		try:
 			self.widget.display(models)
		except:
			pass

	def selectedIds(self):
		return []

