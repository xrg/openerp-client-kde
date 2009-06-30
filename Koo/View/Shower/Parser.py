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

from ShowerView import ShowerView
from Koo.View.AbstractParser import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from Koo.Model import KooModel,KooModelDbg
from Koo.Common import Common
#from Koo.Common.Numeric import *
#from Koo.Common.Calendar import *
from Koo.Common.ViewSettings import *


class ShowerParser(AbstractParser):

	def create(self, viewId, parent, viewModel, rootNode, fields, filter=None):
		self.viewModel = viewModel
		self.filter = filter
		self.widgetList = []

		header = [ {'name': 'name'} ]
		# It's expected that parent will be a Screen
		screen = parent
		attrs = Common.nodeAttributes(rootNode)
		colors = []

		for color_spec in attrs.get('colors', '').split(';'):
			if color_spec:
				colour, test = color_spec.split(':')
				colors.append( ( colour, str(test) ) )
		
		model = KooModelDbg.KooModelDbg( parent )
		#model.setMode( KooModel.KooModel.TreeMode )
		model.setRecordGroup( screen.group )
		model.setFields( fields )
		model.setFieldsOrder( [x['name'] for x in header] )
		model.setColors( colors )
		model.setReadOnly( not attrs.get('editable', False) )

		# view.setOnWriteFunction( attrs.get('on_write', '') )

		view = ShowerView(model, parent )
		#if not view.title:
 		#	view.title = attrs.get('string', 'Unknown' )
		# view.setReadOnly( not attrs.get('editable', False) )

		#if attrs.get('editable', False) == 'top':
		#	view.setAddOnTop( True )

		screen.group.setAllowRecordLoading( False )

		# Create the view
		self.view = view
		self.view.id = viewId
		#self.view.setSvg( 'restaurant.svg' )
		self.view.redraw()
		return self.view


# vim:noexpandtab:
